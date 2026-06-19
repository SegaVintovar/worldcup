"""Reusable UI components for the predictions page."""

from nicegui import ui
from zoneinfo import ZoneInfo
from src.services.database import Match, User, SessionLocal, Prediction
from src.services.prediction_search import get_finished_matches_with_predictions, get_upcoming_predictions
from sqlalchemy import delete

AMSTERDAM = ZoneInfo("Europe/Amsterdam")

WC_TEAMS = sorted([
    "Argentina", "Australia", "Belgium", "Brazil", "Cameroon", "Canada",
    "Chile", "China", "Colombia", "Costa Rica", "Croatia", "Denmark",
    "Ecuador", "Egypt", "England", "France", "Germany", "Ghana",
    "Greece", "Honduras", "Hungary", "Indonesia", "Iran", "Italy",
    "Ivory Coast", "Jamaica", "Japan", "Mexico", "Morocco", "Netherlands",
    "New Zealand", "Nigeria", "Norway", "Panama", "Paraguay", "Peru",
    "Poland", "Portugal", "Romania", "Saudi Arabia", "Senegal", "Serbia",
    "Slovenia", "South Korea", "Spain", "Switzerland", "Turkey", "Ukraine",
    "Uruguay", "USA", "Venezuela",
])


def wire_autocomplete(input_el, suggest_container):
    def on_input():
        val = input_el.value.strip().lower()
        suggest_container.clear()
        if len(val) < 2:
            return
        hits = [t for t in WC_TEAMS if val in t.lower()][:5]
        with suggest_container:
            for team in hits:
                def pick(t=team):
                    input_el.value = t
                    suggest_container.clear()
                ui.button(team, on_click=pick).props("flat dense").classes("w-full text-left text-sm")
    input_el.on("input", on_input)


def build_match_button(match: Match):
    """Returns a styled match button (caller wires up on_click)."""
    btn = ui.button().props("flat").classes(
        "bg-green-50 hover:bg-green-100 text-black border border-green-200 h-full w-full"
    )
    with btn:
        with ui.column().classes("gap-0 items-center w-full"):
            ui.label(f"{match.home_team} vs {match.away_team}").classes("font-semibold text-sm text-center")
            ui.label(
                match.match_date.astimezone(AMSTERDAM).strftime("%d %b %Y %H:%M")
            ).classes("text-xs text-gray-500 text-center")
            if match.stage:
                ui.label(match.stage).classes("text-xs text-gray-400 text-center")
    return btn


def build_rules_card():
    with ui.row().classes("w-full items-center gap-6"):
        with ui.column().classes("gap-1"):
            ui.label("Rules").classes("text-sm font-bold")
            for pts, label in [
                ("3 pts", "Exact score"),
                ("1 pt",  "Correct winner"),
                ("0 pts", "Wrong prediction"),
            ]:
                with ui.row().classes("items-center gap-2"):
                    ui.label(pts).classes("font-bold text-xs w-10 text-green-700")
                    ui.label(label).classes("text-xs")

        with ui.column().classes("gap-1"):
            ui.label("Deadline").classes("text-sm font-bold")
            ui.label("Predictions lock at kickoff.").classes("text-xs text-gray-500")
            ui.label("Tips").classes("text-sm font-bold mt-1")
            ui.label("All times are Amsterdam time (CEST).").classes("text-xs text-gray-500")


def build_finished_matches(current_user: User):
    rows = get_finished_matches_with_predictions(current_user)

    with ui.column().classes("flex-1 gap-2"):
        ui.label("✅ Finished matches").classes("text-xl font-bold")

        if not rows:
            ui.label("No finished matches yet.").classes("text-sm text-gray-400")
            return

        for match, prediction in rows:
            pts = prediction.points_earned if prediction else 0
            pts_color = (
                "text-green-700" if pts == 3
                else "text-yellow-600" if pts == 1
                else "text-red-600"
            )
            with ui.card().classes("w-full p-3 bg-red-50"):
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label(f"{match.home_team} vs {match.away_team}").classes("font-semibold text-sm")
                    ui.label(f"{pts} pts").classes(f"text-xs font-bold {pts_color}")
                ui.label(f"Result: {match.home_score} – {match.away_score}").classes("text-sm mt-1")
                if prediction:
                    ui.label(f"Your pick: {prediction.pred_home_score} – {prediction.pred_away_score}").classes("text-xs text-gray-500")
                else:
                    ui.label("Your pick: None").classes("text-xs text-gray-400 italic")


def del_prediction(prediction: Prediction) -> None:
    db = SessionLocal()
    with db:
        db.execute(delete(Prediction).where(Prediction.id == prediction.id))
        db.commit()
    # db.query(Prediction).filter(Prediction.user_id)

def build_my_predictions(current_user: User):
    upcoming_predictions = get_upcoming_predictions(current_user)

    with ui.column().classes("flex-1 gap-2"):
        ui.label("🔮 My predictions").classes("text-xl font-bold")

        if not upcoming_predictions:
            ui.label("No predictions yet.").classes("text-sm text-gray-400")
            return

        for match, prediction in upcoming_predictions:
            with ui.card().classes("w-full p-3 bg-blue-50"):
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label(f"{match.home_team} vs {match.away_team}").classes("font-semibold text-sm")
                    ui.label(
                        f"{prediction.pred_home_score} – {prediction.pred_away_score}"
                    ).classes("text-base font-bold text-blue-700")
                    ui.button("Delete Prediction", on_click=lambda p=prediction: (del_prediction(p),
                                                                        ui.notify("Deleted", type="positive"),
                                                                           dialog.close()))
                ui.label(
                    match.match_date.astimezone(AMSTERDAM).strftime("%d %b · %H:%M")
                ).classes("text-xs text-gray-500 mt-1")