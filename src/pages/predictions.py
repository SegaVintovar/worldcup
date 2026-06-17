"""Predictions page — logged-in users submit score predictions."""

from nicegui import ui
from src.services.database import Match, User
from src.services.header import header
from src.services.match_calender import get_split_matches
from src.services.prediction_search import (
    get_matches_without_predictions,
    get_finished_matches_with_predictions,
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

# false = no prediction limits (debug mode)
from src.services.prediction_search import PREDICTION_LIMITS


def predictions_page(current_user: User):
    header("/predict")

    ui.query('.nicegui-content').style('background-color: #F5EAD8')

    upcoming, finished = get_split_matches()

    if PREDICTION_LIMITS:
        matches = upcoming
    
    else:
        matches = upcoming + finished


    pred_available = get_matches_without_predictions(current_user, matches)

    pred_ref = {"container": None}

    # ── Prediction form + Rules ───────────────────────────────────────────────
    with ui.row().classes("w-full gap-4 items-stretch"):
        with ui.card().classes("flex-1 p-4"):
            prediction_container = ui.column().classes("w-full")
            pred_ref["container"] = prediction_container
            with prediction_container:
                ui.label("← click a match above to predict").classes("text-sm text-gray-400")

        with ui.card().classes("p-3"):
            build_rules_card()

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
                    get_finished_matches_with_predictions(current_user),
                    get_upcoming_predictions(current_user),
                    search_results_container,
                    lambda match, container: select_match(match, current_user, container),
                    pred_ref,
                )
            )

        with ui.row().classes("w-full gap-2"):
            home_suggest = ui.column().classes("flex-1 gap-0")
            away_suggest = ui.column().classes("flex-1 gap-0")

    wire_autocomplete(home_input, home_suggest)
    wire_autocomplete(away_input, away_suggest)

    search_results_container = ui.column().classes("w-full")

    # ── Available matches ─────────────────────────────────────────────────────
    with ui.card().classes("w-full p-4"):
        ui.label("📅 Available matches").classes("text-xl font-bold mb-2")

        if not pred_available:
            ui.label("No matches available to predict.").classes("text-sm text-gray-400")
        else:
            with ui.grid(columns=3).classes("w-full gap-2"):
                for match in pred_available[:9]:
                    def make_click(m, ref):
                        return lambda: select_match(m, current_user, ref["container"])
                    btn = build_match_button(match)
                    btn.on_click(make_click(match, pred_ref))

    # ── Finished + upcoming predictions ──────────────────────────────────────
    with ui.row().classes("w-full gap-4 mt-2 items-start"):
        build_finished_matches(current_user)
        build_my_predictions(current_user)


# ── Prediction form ───────────────────────────────────────────────────────────

def select_match(match: Match, current_user: User, container):
    container.clear()

    with container:
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(f"{match.home_team} vs {match.away_team}").classes("text-sm font-bold")
            ui.label(
                match.match_date.astimezone(AMSTERDAM).strftime("%d %b %H:%M")
            ).classes("text-xs text-gray-400")

        selected_winner = {"value": None}

        with ui.row().classes("items-center justify-center w-full gap-3 mt-1"):
            ui.label(match.home_team).classes("text-xs text-gray-500 text-right w-24")
            home_num = ui.number(min=0, max=10, value=0).classes("w-16 text-center")
            ui.label("–").classes("text-sm font-bold")
            away_num = ui.number(min=0, max=10, value=0).classes("w-16 text-center")
            ui.label(match.away_team).classes("text-xs text-gray-500 text-left w-24")

        winner_container = ui.row().classes("w-full items-center justify-center gap-2 mt-1")

        def update_winner_selector():
            winner_container.clear()
            if match.phase != "Knockout Phase" or home_num.value != away_num.value:
                selected_winner["value"] = None
                return
            with winner_container:
                ui.label("Winner:").classes("text-xs text-gray-500")
                home_btn = ui.button(match.home_team).props("dense flat")
                away_btn = ui.button(match.away_team).props("dense flat")

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
            ui.navigate.reload()

        ui.button("Save", on_click=on_save).props("dense").classes("mt-1 w-full bg-blue-500 text-white")