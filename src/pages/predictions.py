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
    ).classes("text-2xl font-bold")

    build_available_matches(current_user)


def get_matches_without_predictions(current_user: User, matches: list[Match]) -> list[Match]:
    db = SessionLocal()

    try:
        available_matches: list[Match] = []

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
                available_matches.append(match)

        return available_matches

    finally:
        db.close()


def build_available_matches(current_user: User):
    upcoming, _ = get_split_matches()
    pred_available = get_matches_without_predictions(current_user, upcoming)

    with ui.column().classes("w-1/2 gap-2"):
        ui.label("📅 Available Matches").classes("text-xl font-bold")

        if pred_available:
            buttons = []

            for match in pred_available[:5]:
                btn = ui.button().props('flat').classes(
                    'w-full bg-green-100 hover:bg-green-200 text-black'
                )
                with btn:
                    with ui.column().classes("gap-0 items-center w-full"):  # added items-center w-full
                        ui.label(
                            f"{match.home_team} vs {match.away_team}"
                        ).classes("font-semibold text-sm m-0 leading-tight text-center")  # added text-center

                        ui.label(
                            match.match_date.astimezone(AMSTERDAM)
                            .strftime("%d %b %Y %H:%M")
                        ).classes("text-xs text-gray-600 m-0 leading-tight text-center")  # added text-center

                        if match.stage:
                            ui.label(match.stage).classes(
                                "text-xs text-gray-400 m-0 leading-tight text-center"  # added text-center
                            )

                buttons.append((btn, match))


            prediction_container = ui.column().classes('w-full')

            # --- Pass 2: now that prediction_container exists, wire the clicks ---
            for btn, match in buttons:
                btn.on_click(lambda m=match: select_match(m, prediction_container))


def select_match(match: Match, container):
    # Unchanged from your original
    container.clear()

    with container:
        with ui.card().classes("w-full p-4 bg-green-50"):

            ui.label(f"{match.home_team} vs {match.away_team}")\
                .classes("text-xl font-bold")

            ui.label(
                match.match_date.astimezone(AMSTERDAM)
                .strftime("%d %b %Y %H:%M")
            ).classes("text-sm text-gray-500")

            ui.separator()

            with ui.row().classes("items-center justify-between w-full mt-4"):

                ui.number(
                    label=match.home_team,
                    min=0,
                    max=20,
                ).classes("w-24")

                ui.label("vs").classes("text-lg font-bold")

                ui.number(
                    label=match.away_team,
                    min=0,
                    max=20,
                ).classes("w-24")

            ui.separator()

            ui.button(
                "Save prediction",
                on_click=lambda: ui.notify("Saved (not wired yet)"),
            ).classes("mt-4 w-full bg-blue-500 text-white")