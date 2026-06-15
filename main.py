import os
import logging
from nicegui import ui, app
from fastapi import Request
from fastapi.responses import RedirectResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone

# pages
from src.pages.login import login_page
from src.pages.predictions import predictions_page
from src.pages.leaderboard import leaderboard_page
from src.pages.dashboard import dashboard_page

# services
from src.services.database import init_db, SessionLocal, User, Match, Prediction
from src.services.auth import exchange_code_for_user
from src.services.header import header
from src.services.scoring import update_prediction_scores, update_user_scores

# outsourced
from src.results.football_api import sync_matches_to_db, update_matches

from zoneinfo import ZoneInfo

AMSTERDAM = ZoneInfo("Europe/Amsterdam")


DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"

LAST_SYNC = None

scheduler = AsyncIOScheduler()


# ── Daily sync job ────────────────────────────────────────────────────────────

def daily_sync() -> None:
    """Sync matches from the API, then score any newly finished ones."""

    global LAST_SYNC
    db = SessionLocal()
    try:
        match_count = db.query(Match).count()
        if match_count == 0:
            sync_matches_to_db(db)
        else:
            update_matches(db)
        print("sync and update was done", flush=True)
    finally:
        db.close()
    update_prediction_scores()
    update_user_scores()

    LAST_SYNC = datetime.now(timezone.utc)

# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_startup
async def startup():
    init_db()
    db = SessionLocal()
    try:
        match_count = db.query(Match).count()
        if match_count == 0:
            sync_matches_to_db(db)
        else:
            update_matches(db)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    update_prediction_scores()
    update_user_scores()
    # Schedule daily sync at 03:00, scoring at 03:30 (Amsterdam time)
    scheduler.add_job(daily_sync, "cron", hour="*/2", minute=0, timezone="Europe/Amsterdam")
    scheduler.start()



# ── OAuth callback ────────────────────────────────────────────────────────────

@app.get("/auth/callback")
async def oauth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return RedirectResponse("/")

    try:
        profile = await exchange_code_for_user(code)
    except Exception as e:
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