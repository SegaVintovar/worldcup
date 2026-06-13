"""Predictions page — logged-in users submit score predictions."""

from nicegui import ui
from src.services.database import SessionLocal, Match, Prediction, User
from src.services.header import header
from src.services.match_calender import get_split_matches
from zoneinfo import ZoneInfo

AMSTERDAM = ZoneInfo("Europe/Amsterdam")


def predictions_page(current_user: User):
    header("/predict")

    ui.label(
        f"Hello {current_user.login_42}, create your predictions below"
    ).classes("text-2xl font-bold mb-4")

    with ui.row().classes("w-full gap-4 items-start"):
        build_available_matches(current_user)
        build_finished_matches(current_user)
        build_my_predictions(current_user)


# ── Data helpers ─────────────────────────────────────────────────────────────

def get_matches_without_predictions(current_user: User, matches: list[Match]) -> list[Match]:
    db = SessionLocal()
    try:
        available: list[Match] = []
        for match in matches:
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


def get_finished_predictions(current_user: User) -> list[tuple[Match, Prediction]]:
    """Returns (match, prediction) pairs for played matches where user has a prediction."""
    db = SessionLocal()
    try:
        results = (
            db.query(Match, Prediction)
            .join(Prediction, Prediction.match_id == Match.id)
            .filter(
                Prediction.user_id == current_user.id,
                Match.played == True,
            )
            .order_by(Match.match_date.desc())
            .limit(5)
            .all()
        )
        return results
    finally:
        db.close()


def get_upcoming_predictions(current_user: User) -> list[tuple[Match, Prediction]]:
    """Returns (match, prediction) pairs for upcoming matches where user has a prediction."""
    db = SessionLocal()
    try:
        results = (
            db.query(Match, Prediction)
            .join(Prediction, Prediction.match_id == Match.id)
            .filter(
                Prediction.user_id == current_user.id,
                Match.played == False,
            )
            .order_by(Match.match_date.asc())
            .limit(5)
            .all()
        )
        return results
    finally:
        db.close()


# ── Column builders ───────────────────────────────────────────────────────────

def build_available_matches(current_user: User):
    upcoming, _ = get_split_matches()
    pred_available = get_matches_without_predictions(current_user, upcoming)

    with ui.column().classes("flex-1 gap-2 min-w-0"):
        ui.label("📅 Available matches").classes("text-xl font-bold")

        if not pred_available:
            ui.label("No matches available to predict.").classes("text-sm text-gray-400")
            return

        buttons = []
        for match in pred_available[:5]:
            btn = ui.button().props("flat").classes(
                "w-full bg-green-100 hover:bg-green-200 text-black"
            )
            with btn:
                with ui.column().classes("gap-0 items-center w-full"):
                    ui.label(f"{match.home_team} vs {match.away_team}").classes(
                        "font-semibold text-sm m-0 leading-tight text-center"
                    )
                    ui.label(
                        match.match_date.astimezone(AMSTERDAM).strftime("%d %b %Y %H:%M")
                    ).classes("text-xs text-gray-600 m-0 leading-tight text-center")
                    if match.stage:
                        ui.label(match.stage).classes(
                            "text-xs text-gray-400 m-0 leading-tight text-center"
                        )
            buttons.append((btn, match))

        prediction_container = ui.column().classes("w-full")

        for btn, match in buttons:
            btn.on_click(lambda m=match: select_match(m, prediction_container))


def build_finished_matches(current_user: User):
    finished = get_finished_predictions(current_user)

    with ui.column().classes("flex-1 gap-2 min-w-0"):
        ui.label("✅ Finished matches").classes("text-xl font-bold")

        if not finished:
            ui.label("No finished matches yet.").classes("text-sm text-gray-400")
            return

        for match, prediction in finished:
            with ui.card().classes("w-full p-3 bg-red-50"):
                with ui.row().classes("justify-between items-center w-full"):
                    ui.label(f"{match.home_team} vs {match.away_team}").classes(
                        "font-semibold text-sm"
                    )
                    points = prediction.points_earned or 0
                    badge_color = (
                        "bg-green-200 text-green-800" if points > 0
                        else "bg-gray-200 text-gray-600"
                    )
                    ui.label(f"{points} pts").classes(
                        f"text-xs font-bold px-2 py-1 rounded {badge_color}"
                    )

                # Final score
                ui.label(
                    f"Result: {match.home_score} – {match.away_score}"
                ).classes("text-sm font-bold text-gray-700")

                # User's prediction
                ui.label(
                    f"Your prediction: {prediction.pred_home_score} – {prediction.pred_away_score}"
                ).classes("text-xs text-gray-500")

                ui.label(
                    match.match_date.astimezone(AMSTERDAM).strftime("%d %b %Y")
                ).classes("text-xs text-gray-400")


def build_my_predictions(current_user: User):
    upcoming_predictions = get_upcoming_predictions(current_user)

    with ui.column().classes("flex-1 gap-2 min-w-0"):
        ui.label("🔮 My predictions").classes("text-xl font-bold")

        if not upcoming_predictions:
            ui.label("No predictions submitted yet.").classes("text-sm text-gray-400")
            return

        for match, prediction in upcoming_predictions:
            with ui.card().classes("w-full p-3 bg-blue-50"):
                ui.label(f"{match.home_team} vs {match.away_team}").classes(
                    "font-semibold text-sm"
                )
                ui.label(
                    f"{prediction.pred_home_score} – {prediction.pred_away_score}"
                ).classes("text-lg font-bold text-blue-700")
                ui.label(
                    match.match_date.astimezone(AMSTERDAM).strftime("%d %b %Y %H:%M")
                ).classes("text-xs text-gray-400")
                if match.stage:
                    ui.label(match.stage).classes("text-xs text-gray-400")


# ── Prediction form ───────────────────────────────────────────────────────────

def select_match(match: Match, container):
    container.clear()

    with container:
        with ui.card().classes("w-full p-4 bg-green-50"):
            ui.label(f"{match.home_team} vs {match.away_team}").classes("text-xl font-bold")
            ui.label(
                match.match_date.astimezone(AMSTERDAM).strftime("%d %b %Y %H:%M")
            ).classes("text-sm text-gray-500")
            ui.separator()

            with ui.row().classes("items-center justify-between w-full mt-4"):
                ui.number(label=match.home_team, min=0, max=20).classes("w-24")
                ui.label("vs").classes("text-lg font-bold")
                ui.number(label=match.away_team, min=0, max=20).classes("w-24")

            ui.separator()
            ui.button(
                "Save prediction",
                on_click=lambda: ui.notify("Saved (not wired yet)"),
                
                ).classes("mt-4 w-full bg-blue-500 text-white")

def save_prediction(user_id, match_id, home_goals, away_goals, winner):
    ui.notify("Saving... Ooops, DB not connected yet.")
    db = SessionLocal()

    ...