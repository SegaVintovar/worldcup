"""Predictions page — logged-in users submit score predictions."""

from nicegui import ui
from src.services.database import Match, User
from src.services.header import header
from src.services.match_calender import get_split_matches
from src.services.prediction_search import (
    get_matches_without_predictions,
    get_finished_predictions,
    get_upcoming_predictions,
    save_prediction,
    run_search,
)
from src.services.prediction_components import (
    wire_autocomplete,
    build_match_button,
    build_rules_card,
    build_finished_matches,
    build_my_predictions,
    AMSTERDAM,
)


def predictions_page(current_user: User):
    header("/predict")

    upcoming, _ = get_split_matches()
    pred_available = get_matches_without_predictions(current_user, upcoming)

    search = {"home": "", "away": ""}

    # ── Search bar ────────────────────────────────────────────────────────────
    with ui.card().classes("w-full p-3"):
        with ui.row().classes("w-full items-end gap-2"):
            home_input = ui.input(label="Home team", placeholder="e.g. Netherlands").classes("flex-1")
            away_input = ui.input(label="Away team", placeholder="e.g. Argentina").classes("flex-1")

            ui.button("Search", icon="search").classes("mb-1").on_click(
                lambda: run_search(
                    home_input.value,
                    away_input.value,
                    pred_available,
                    get_finished_predictions(current_user),
                    get_upcoming_predictions(current_user),
                    search_results_container,
                )
            )

        with ui.row().classes("w-full gap-2"):
            home_suggest = ui.column().classes("flex-1 gap-0")
            away_suggest = ui.column().classes("flex-1 gap-0")

    wire_autocomplete(home_input, home_suggest)
    wire_autocomplete(away_input, away_suggest)

    search_results_container = ui.column().classes("w-full")

    pred_ref = {"container": None}

    # ── Available matches ─────────────────────────────────────────────────────
    with ui.card().classes("w-full p-4"):
        ui.label("📅 Available matches").classes("text-xl font-bold mb-2")

        if not pred_available:
            ui.label("No matches available to predict.").classes("text-sm text-gray-400")
        else:
            with ui.grid(columns=3).classes("w-full gap-2"):
                for match in pred_available[:9]:
                    def make_click(m, ref):
                        return lambda: select_match(m, current_user,ref["container"])
                    btn = build_match_button(match)
                    btn.on_click(make_click(match, pred_ref))

    # ── Prediction form + Rules ───────────────────────────────────────────────
    with ui.row().classes("w-full gap-4 items-stretch"):
        with ui.card().classes("flex-1 p-4 min-h-[220px]"):
            prediction_container = ui.column().classes("w-full")
            pred_ref["container"] = prediction_container
            with prediction_container:
                ui.label("← click a match above to predict").classes("text-sm text-gray-400")

        with ui.card().classes("flex-1 p-4"):
            build_rules_card()

    # ── Finished + upcoming predictions ──────────────────────────────────────
    with ui.row().classes("w-full gap-4 mt-2 items-start"):
        build_finished_matches(current_user)
        build_my_predictions(current_user)


# ── Prediction form ───────────────────────────────────────────────────────────

def select_match(match: Match, current_user: User, container):
    container.clear()

    with container:
        ui.label(f"{match.home_team} vs {match.away_team}").classes("text-lg font-bold")
        ui.label(
            match.match_date.astimezone(AMSTERDAM).strftime("%d %b %Y %H:%M")
        ).classes("text-xs text-gray-500 mb-2")

        ui.separator()

        selected_winner = {"value": None}

        with ui.row().classes("items-end justify-center w-full gap-6 mt-4"):
            with ui.column().classes("items-center gap-1"):
                ui.label(match.home_team).classes("text-xs text-gray-500")
                home_num = ui.number(min=0, max=10, value=0).classes("w-20 text-center")

            ui.label("vs").classes("text-lg font-bold pb-1")

            with ui.column().classes("items-center gap-1"):
                ui.label(match.away_team).classes("text-xs text-gray-500")
                away_num = ui.number(min=0, max=10, value=0).classes("w-20 text-center")

        ui.separator().classes("mt-4")

        winner_container = ui.column().classes("w-full items-center mt-2")

        def update_winner_selector():
            winner_container.clear()

            if match.phase != "Knockout Phase" or home_num.value != away_num.value:
                selected_winner["value"] = None
                return

            with winner_container:
                ui.label("Select advancing team").classes("text-sm text-gray-500")

                with ui.row().classes("gap-4"):
                    home_btn = ui.button(match.home_team)
                    away_btn = ui.button(match.away_team)

                    def select_home():
                        selected_winner["value"] = match.home_team
                        home_btn.props("color=positive")
                        away_btn.props("color=grey")

                    def select_away():
                        selected_winner["value"] = match.away_team
                        away_btn.props("color=positive")
                        home_btn.props("color=grey")

                    home_btn.on("click", lambda _: select_home())
                    away_btn.on("click", lambda _: select_away())

        home_num.on("update:model-value", lambda _: update_winner_selector())
        away_num.on("update:model-value", lambda _: update_winner_selector())

        def on_save():
            home_score = int(home_num.value)
            away_score = int(away_num.value)

            if (
                match.phase == "Knockout Phase"
                and home_score == away_score
                and not selected_winner["value"]
            ):
                ui.notify("Can't have a draw in Knockout Phase. Pick a winner.", color="negative")
                return

            save_prediction(current_user, match, home_score, away_score, selected_winner["value"])
            ui.notify("Prediction saved!", color="positive")

        ui.button("Save prediction", on_click=on_save).classes("mt-4 w-full bg-blue-500 text-white")