"""DB queries and search logic for predictions."""

from datetime import datetime
from nicegui import ui
from zoneinfo import ZoneInfo
from src.services.database import SessionLocal, Match, Prediction, User

AMSTERDAM = ZoneInfo("Europe/Amsterdam")

from src.services.state import PREDICTION_LIMITS, KO_ONLY, CONFIRMED_ONLY


def teams_confirmed(match: Match) -> bool:
    return not any(char.isdigit() for char in match.home_team + match.away_team)

def get_matches_without_predictions(current_user: User, matches: list[Match]) -> list[Match]:
    db = SessionLocal()
    now = datetime.now(AMSTERDAM)

    try:
        available: list[Match] = []

        for match in matches:

            if CONFIRMED_ONLY and not teams_confirmed(match):
                continue

            if KO_ONLY and match.phase != "Knockout Phase":
                continue

            # Production mode: no predictions after kickoff
            if PREDICTION_LIMITS:
                match_time = match.match_date.astimezone(AMSTERDAM)

                if match.played:
                    continue

                if match_time <= now:
                    continue

            prediction = (
                db.query(Prediction)
                .filter(
                    Prediction.user_id == current_user.id,
                    Prediction.match_id == match.id,
                )
                .first()
            )

            if prediction is None:
                available.append(match)

        return available

    finally:
        db.close()


def get_finished_matches_with_predictions(current_user: User) -> list[tuple[Match, Prediction | None]]:
    """All finished matches, with the user's prediction if they made one (else None)."""
    db = SessionLocal()

    try:
        query = (
            db.query(Match)
            .filter(Match.played == True)
        )

        if KO_ONLY:
            query = query.filter(
                Match.phase == "Knockout Phase"
            )

        matches = (
            query
            .order_by(Match.match_date.desc())
            .limit(5)
            .all()
        )

        if CONFIRMED_ONLY:
            matches = [
                match for match in matches
                if teams_confirmed(match)
            ]

        result = []

        for match in matches:
            prediction = (
                db.query(Prediction)
                .filter(
                    Prediction.user_id == current_user.id,
                    Prediction.match_id == match.id,
                )
                .first()
            )

            result.append((match, prediction))

        return result

    finally:
        db.close()


# Keep old name as alias so nothing else breaks
def get_finished_predictions(current_user: User):
    return [(m, p) for m, p in get_finished_matches_with_predictions(current_user) if p is not None]


def get_upcoming_predictions(current_user: User) -> list[tuple[Match, Prediction]]:
    db = SessionLocal()
    try:
        query = (
            db.query(Match, Prediction)
            .join(Prediction, Prediction.match_id == Match.id)
            .filter(Prediction.user_id == current_user.id)
        )

        if PREDICTION_LIMITS:
            query = query.filter(Match.played == False)

        return (
            query
            .order_by(Match.match_date.asc())
            .all()
        )

    finally:
        db.close()


def save_prediction(
    current_user: User,
    match: Match,
    home_score: int,
    away_score: int,
    winner: str | None = None,
):
    db = SessionLocal()
    try:
        existing = (
            db.query(Prediction)
            .filter(Prediction.user_id == current_user.id, Prediction.match_id == match.id)
            .first()
        )

        if existing:
            existing.pred_home_score = home_score
            existing.pred_away_score = away_score
            existing.winner = winner
        else:
            db.add(Prediction(
                user_id=current_user.id,
                match_id=match.id,
                pred_home_score=home_score,
                pred_away_score=away_score,
                winner=winner,
            ))

        db.commit()
    finally:
        db.close()


def run_search(home_val, away_val, available, finished, upcoming, container, on_select, pred_ref):
    container.clear()
    h = home_val.strip().lower()
    a = away_val.strip().lower()
    if not h and not a:
        return

    def matches_search(home_team: str, away_team: str) -> bool:
        ht, at = home_team.lower(), away_team.lower()
        return (not h or h in ht or h in at) and (not a or a in ht or a in at)

    with container:
        with ui.card().classes("w-full p-4"):
            ui.label("🔍 Search results").classes("text-lg font-bold mb-2")

            found_any = False

            avail_hits = [m for m in available if matches_search(m.home_team, m.away_team)]
            if avail_hits:
                found_any = True
                ui.label("Available to predict").classes("text-sm font-semibold text-gray-500 mt-2 mb-1")
                for m in avail_hits:
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label(
                            f"{m.home_team} vs {m.away_team} · "
                            f"{m.match_date.astimezone(AMSTERDAM).strftime('%d %b %H:%M')}"
                        ).classes("text-sm")
                        ui.button("Select", on_click=lambda _, match=m: on_select(match, pred_ref["container"])) \
                            .props("flat dense").classes("text-xs text-green-700")

            fin_hits = [(m, p) for m, p in finished if matches_search(m.home_team, m.away_team)]
            if fin_hits:
                found_any = True
                ui.label("Finished").classes("text-sm font-semibold text-gray-500 mt-3 mb-1")
                for m, p in fin_hits:
                    pick = f"{p.pred_home_score}–{p.pred_away_score}" if p else "None"
                    pts = p.points_earned or 0 if p else 0
                    ui.label(
                        f"{m.home_team} vs {m.away_team} · "
                        f"Result {m.home_score}–{m.away_score} · "
                        f"Your pick {pick} · {pts} pts"
                    ).classes("text-sm")

            up_hits = [(m, p) for m, p in upcoming if matches_search(m.home_team, m.away_team)]
            if up_hits:
                found_any = True
                ui.label("Your predictions").classes("text-sm font-semibold text-gray-500 mt-3 mb-1")
                for m, p in up_hits:
                    ui.label(
                        f"{m.home_team} vs {m.away_team} · "
                        f"Your pick: {p.pred_home_score}–{p.pred_away_score}"
                    ).classes("text-sm")

            if not found_any:
                ui.label("No matches found.").classes("text-sm text-gray-400")