import os
import logging
from nicegui import ui, app
from fastapi import Request
from fastapi.responses import RedirectResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# pages
from src.pages.login import login_page
from src.pages.predictions import predictions_page
from src.pages.leaderboard import leaderboard_page
from src.pages.dashboard import dashboard_page

# services
from src.services.database import init_db, SessionLocal, User, Match, Prediction
from src.services.auth import exchange_code_for_user
from src.services.header import header

# outsourced
from src.results.football_api import sync_matches_to_db, update_matches

logger = logging.getLogger(__name__)

DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"

scheduler = AsyncIOScheduler()


# ── Scoring logic ─────────────────────────────────────────────────────────────

def score_predictions() -> None:
    """
    For every prediction on a finished match that hasn't been scored yet,
    calculate points and update the prediction + the user's total score.

    Points:
        3 — exact score (e.g. predicted 2-1, result 2-1)
        1 — correct winner / draw (e.g. predicted 2-0, result 3-0)
        0 — wrong
    """
    db = SessionLocal()
    try:
        # Only look at predictions for matches that are now finished
        # and where points_earned is still 0 AND the match has a real result
        unscored = (
            db.query(Prediction)
            .join(Match)
            .filter(
                Match.played == True,
                Match.home_score != None,
                Match.away_score != None,
                Prediction.points_earned == 0,
            )
            .all()
        )

        if not unscored:
            logger.info("score_predictions: nothing to score.")
            return

        users_to_update: dict[int, int] = {}  # user_id -> extra points

        for pred in unscored:
            match = pred.match
            ph, pa = pred.pred_home_score, pred.pred_away_score
            rh, ra = match.home_score, match.away_score

            if ph == rh and pa == ra:
                pts = 3  # exact score
            elif (ph - pa) == (rh - ra):
                pts = 1  # correct draw (0-0 predicted, 0-0 result handled above)
            elif (ph > pa) == (rh > ra):
                pts = 1  # correct winner
            else:
                pts = 0

            pred.points_earned = pts
            users_to_update[pred.user_id] = users_to_update.get(pred.user_id, 0) + pts

        # Bulk-update user scores
        for user_id, extra in users_to_update.items():
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                user.p_score = (user.p_score or 0) + extra

        db.commit()
        logger.info(
            f"score_predictions: scored {len(unscored)} predictions "
            f"across {len(users_to_update)} users."
        )

    except Exception as e:
        db.rollback()
        logger.error(f"score_predictions failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ── Daily sync job ────────────────────────────────────────────────────────────

def daily_sync() -> None:
    """Sync matches from the API, then score any newly finished ones."""
    logger.info("daily_sync: starting match sync...")
    db = SessionLocal()
    try:
        sync_matches_to_db(db)
    finally:
        db.close()
    logger.info("daily_sync: scoring predictions...")
    score_predictions()
    logger.info("daily_sync: done.")


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_startup
async def startup():
    init_db()
    db = SessionLocal()
    try:
        match_count = db.query(Match).count()
        if match_count == 0:
            logger.info("No matches found, syncing from API...")
            sync_matches_to_db(db)
            logger.info(f"Sync done. {db.query(Match).count()} matches in DB.")
        else:
            logger.info(f"Database ready. ({match_count} matches already loaded)")
    except Exception as e:
        logger.error(f"Startup sync failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    # Score any predictions that were left unscored (e.g. after a restart)
    score_predictions()

    # Schedule daily sync at 03:00, scoring at 03:30 (Amsterdam time)
    scheduler.add_job(daily_sync, "cron", hour=3, minute=0, timezone="Europe/Amsterdam")
    scheduler.start()
    logger.info("Scheduler started. Daily sync at 03:00 Amsterdam time.")


# ── OAuth callback ────────────────────────────────────────────────────────────

@app.get("/auth/callback")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return RedirectResponse("/")

    try:
        profile = await exchange_code_for_user(code)
    except Exception as e:
        logger.error(f"OAuth exchange failed: {e}")
        return RedirectResponse("/")

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(login_42=profile["login"]).first()
        if not user:
            user = User(
                login_42=profile["login"],
                avatar_url=profile.get("image", {}).get("link"),
            )
            db.add(user)
        else:
            user.avatar_url = profile.get("image", {}).get("link")

        db.commit()
        db.refresh(user)
        app.storage.user["user_id"] = user.id
    finally:
        db.close()

    return RedirectResponse("/dashboard")


# ── Routes ────────────────────────────────────────────────────────────────────

def get_current_user() -> User | None:
    user_id = app.storage.user.get("user_id")
    if not user_id:
        return None
    db = SessionLocal()
    try:
        return db.query(User).filter_by(id=user_id).first()
    finally:
        db.close()


@ui.page("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        ui.navigate.to("/")
    else:
        dashboard_page(user)


@ui.page("/")
def index():
    user = get_current_user()
    if user:
        ui.navigate.to("/dashboard")
    else:
        login_page()


@ui.page("/predict")
def predict():
    user = get_current_user()
    if not user:
        ui.navigate.to("/")
    else:
        predictions_page(user)


@ui.page("/leaderboard")
def leaderboard():
    user = get_current_user()
    if not user:
        ui.navigate.to("/")
    else:
        leaderboard_page()


# ── Run ───────────────────────────────────────────────────────────────────────

ui.run(
    host="0.0.0.0",
    port=8080,
    title="Football Predictor",
    favicon="⚽",
    storage_secret=os.environ.get("APP_SECRET_KEY", "dev-secret"),
    reload=False
)