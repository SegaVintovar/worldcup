"""Predictions page — logged-in users submit score predictions."""

from nicegui import ui, app
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
from src.services.state import PREDICTION_LIMITS
from datetime import datetime
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
app.add_static_files("/assets", str(ASSETS_DIR))



def predictions_page(current_user: User):
    header("/predict")

    ui.query('.nicegui-content').style('background-color: #F5EAD8')
    with ui.row().classes("w-full gap-4 items-stretch"):
        ui.add_css('''
        .q-message-avatar {
            width: 64px !important;
            height: 64px !important;
            border: 2px solid #444 !important;
        }
        ''')
        with ui.card():
            ui.chat_message((
                'On this page you can make your prediction\n',
                'Find the match with our search bar or pick one from next 9 avaliable matches.',
                'You can always delete predictions before kickoff time.'),
                name='SQoot',
                avatar='/assets/owl_prediction_mascot.png').classes('flex')

        with ui.card().classes("flex-1 p-3"):
            build_rules_card()

    upcoming, finished = get_split_matches()

    if PREDICTION_LIMITS:
        matches = upcoming

    else:
        matches = upcoming + finished


    pred_available = get_matches_without_predictions(current_user, matches)

    # filter out matches that have already started
    try:
        now = datetime.now(AMSTERDAM)
        pred_available = [m for m in pred_available if m.match_date.astimezone(AMSTERDAM) > now]
    except Exception:
        # if something goes wrong with timezones or match_date, fall back to original list
        pass

    pred_ref = {
        "container": None,
        "selected_match": None,
        "search_card": None,
        "available_card": None,
        "search_results_container": None,
    }

    def on_search_select(match, container):
        pred_ref["selected_match"] = match
        if pred_ref.get("search_card"):
            pred_ref["search_card"].style("display:none")
        if pred_ref.get("available_card"):
            pred_ref["available_card"].style("display:none")
        if pred_ref.get("search_results_container"):
            pred_ref["search_results_container"].style("display:none")
        select_match(match, current_user, container, pred_ref)


    home_input = None
    away_input = None

    ui.label("Step 1: Select the match").classes('text-xl font-bold mb-2')

    # ── Search bar ────────────────────────────────────────────────────────────
    
    search_card = ui.card().classes("w-full p-3")
    pred_ref["search_card"] = search_card
    with search_card:
        ui.label("🔍 Search Bar").classes("text-xl font-bold mb-2")
        with ui.row().classes("w-full items-end gap-2"):
            home_input = ui.input(label="Home team", placeholder="e.g. Netherlands").classes("flex-1")
            away_input = ui.input(label="Away team", placeholder="e.g. Argentina").classes("flex-1")

            def on_search_click():
                run_search(
                    home_input.value,
                    away_input.value,
                    pred_available,
                    get_finished_matches_with_predictions(current_user),
                    get_upcoming_predictions(current_user),
                    search_results_container,
                    lambda match, container: on_search_select(match, container),
                    pred_ref,
                )

            ui.button("Search", icon="search").classes("mb-1").on_click(on_search_click)

        with ui.row().classes("w-full gap-2"):
            home_suggest = ui.column().classes("flex-1 gap-0")
            away_suggest = ui.column().classes("flex-1 gap-0")

    wire_autocomplete(home_input, home_suggest)
    wire_autocomplete(away_input, away_suggest)

    search_results_container = ui.column().classes("w-full")
    pred_ref["search_results_container"] = search_results_container

    # ui.label("Or").classes('text-l font-bold mb-2')


    # ── Available matches ─────────────────────────────────────────────────────
    # pagination state for available matches
    page = {"num": 0, "per_page": 9}

    def render_matches(matches_container):
        matches_container.clear()
        start = page["num"] * page["per_page"]
        end = start + page["per_page"]
        subset = pred_available[start:end]
        if not subset:
            ui.label("No matches available to predict.").classes("text-sm text-gray-400")
            return
        with matches_container:
            with ui.grid(columns=3).classes("w-full gap-2"):
                for match in subset:
                    def make_click(m, ref):
                        def handler():
                            ref["selected_match"] = m
                            if ref.get("search_card"):
                                ref["search_card"].style("display:none")
                            if ref.get("available_card"):
                                ref["available_card"].style("display:none")
                            if ref.get("search_results_container"):
                                ref["search_results_container"].style("display:none")
                            select_match(m, current_user, ref["container"], ref)

                        return handler

                    btn = build_match_button(match)
                    btn.on_click(make_click(match, pred_ref))

    available_card = ui.card().classes("w-full p-4")
    pred_ref["available_card"] = available_card
    with available_card:
        ui.label("📅 Available matches").classes("text-xl font-bold mb-2")

        matches_container = ui.column().classes("w-full")
        pred_ref["matches_container"] = matches_container

        # pagination controls
        def go_prev():
            if page["num"] > 0:
                page["num"] -= 1
                render_matches(matches_container)
                total = max(1, (len(pred_available) + page["per_page"] - 1) // page["per_page"])
                try:
                    page_label.set_text(f"Page {page['num'] + 1} / {total}")
                except Exception:
                    pass

        def go_next():
            if (page["num"] + 1) * page["per_page"] < len(pred_available):
                page["num"] += 1
                render_matches(matches_container)
                total = max(1, (len(pred_available) + page["per_page"] - 1) // page["per_page"])
                try:
                    page_label.set_text(f"Page {page['num'] + 1} / {total}")
                except Exception:
                    pass

        render_matches(matches_container)

        with ui.row().classes("w-full items-center justify-center gap-4 mt-2"):
            prev_btn = ui.button("Prev").props("flat")
            prev_btn.on_click(lambda: go_prev())
            page_label = ui.label(f"Page {page['num'] + 1} / {max(1, (len(pred_available) + page['per_page'] - 1) // page['per_page'])}")
            next_btn = ui.button("Next").props("flat")
            next_btn.on_click(lambda: go_next())

    ui.label("Step 2: Predict the result").classes("text-xl font-bold mb-2")
    
     # ── Prediction form ───────────────────────────────────────────────
    with ui.row().classes("w-full gap-4 items-stretch"):
        with ui.card().classes("flex-1 p-4"):
            # anchor for scrolling into view when a match is selected
            ui.html('<div id="prediction_anchor"></div>')
            prediction_container = ui.column().classes("w-full")
            pred_ref["container"] = prediction_container
            with prediction_container:
                ui.label("Choose a match to predict").classes("text-sm text-gray-400")



    # ── Finished + upcoming predictions ──────────────────────────────────────
    with ui.row().classes("w-full gap-4 mt-2 items-start"):
        build_finished_matches(current_user)
        build_my_predictions(current_user)


# ── Prediction form ───────────────────────────────────────────────────────────

def select_match(match: Match, current_user: User, container, pred_ref=None):
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
        def on_cancel():
            if pred_ref is not None:
                pred_ref["selected_match"] = None
                if pred_ref.get("search_card"):
                    pred_ref["search_card"].style("display:block")
                if pred_ref.get("available_card"):
                    pred_ref["available_card"].style("display:block")
                if pred_ref.get("search_results_container"):
                    pred_ref["search_results_container"].style("display:block")
            container.clear()
            with container:
                ui.label("Choose a match to predict").classes("text-sm text-gray-400")

        ui.button("Cancel", on_click=on_cancel).props("flat").classes("mt-1 w-full")
        ui.button("Save", on_click=on_save).props("dense").classes("mt-1 w-full bg-blue-500 text-white")
        # scroll to prediction form anchor
        try:
            ui.run_javascript("document.getElementById('prediction_anchor').scrollIntoView({behavior: 'smooth'});")
        except Exception:
            pass