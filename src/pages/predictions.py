"""Predictions page — logged-in users submit score predictions."""

from nicegui import ui
from src.services.database import Match, User
from src.services.header import header
from src.services.match_calender import get_split_matches
from src.services.prediction_management import (
    get_matches_without_predictions,
    get_finished_predictions,
    get_upcoming_predictions,
    save_prediction,
)
from zoneinfo import ZoneInfo

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


def predictions_page(current_user: User):
    header("/predict")

    upcoming, _ = get_split_matches()
    pred_available = get_matches_without_predictions(current_user, upcoming)

    # search state — plain dicts, no ui.state needed
    search = {"home": "", "away": ""}

    # ── Search bar ────────────────────────────────────────────────────────────
    with ui.card().classes("w-full p-3"):
        with ui.row().classes("w-full items-end gap-2"):
            home_input = ui.input(
                label="Home team", placeholder="e.g. Netherlands"
            ).classes("flex-1")

            away_input = ui.input(
                label="Away team", placeholder="e.g. Argentina"
            ).classes("flex-1")

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

        # autocomplete rows sit below inputs, outside the row
        with ui.row().classes("w-full gap-2"):
            home_suggest = ui.column().classes("flex-1 gap-0")
            away_suggest = ui.column().classes("flex-1 gap-0")

    wire_autocomplete(home_input, home_suggest)
    wire_autocomplete(away_input, away_suggest)

    # search results area (hidden until search runs)
    search_results_container = ui.column().classes("w-full")

    # ── mutable reference so buttons can find the container after it's created
    pred_ref = {"container": None}

    # ── Available matches ───────────────────────────────────────────────
    with ui.card().classes("w-full p-4"):
        ui.label("📅 Available matches").classes("text-xl font-bold mb-2")

        if not pred_available:
            ui.label("No matches available to predict.").classes("text-sm text-gray-400")
        else:
            with ui.grid(columns=3).classes("w-full gap-2"):
                for match in pred_available[:9]:
                    btn = ui.button().props("flat").classes(
                        "bg-green-50 hover:bg-green-100 text-black border border-green-200 h-full w-full"
                    )
                    with btn:
                        with ui.column().classes("gap-0 items-center w-full"):
                            ui.label(f"{match.home_team} vs {match.away_team}").classes(
                                "font-semibold text-sm text-center"
                            )
                            ui.label(
                                match.match_date.astimezone(AMSTERDAM).strftime("%d %b %Y %H:%M")
                            ).classes("text-xs text-gray-500 text-center")
                            if match.stage:
                                ui.label(match.stage).classes("text-xs text-gray-400 text-center")
                    
                    def make_click(m, ref):
                        return lambda: select_match(m, ref["container"])
                    
                    btn.on_click(make_click(match, pred_ref))

    # ── Prediction form + Rules ─────────────────────────────────────────
    with ui.row().classes("w-full gap-4 items-stretch"):

        # LEFT
        with ui.card().classes("flex-1 p-4 min-h-[220px]"):
            prediction_container = ui.column().classes("w-full")
            pred_ref["container"] = prediction_container
            with prediction_container:
                ui.label("← click a match above to predict").classes(
                    "text-sm text-gray-400"
                )

        # RIGHT
        with ui.card().classes("flex-1 p-4"):
            build_rules_card()

    # ── Finished + upcoming predictions ──────────────────────────────────────
    with ui.row().classes("w-full gap-4 mt-2 items-start"):
        build_finished_matches(current_user)
        build_my_predictions(current_user)


# ── UI helpers ────────────────────────────────────────────────────────────────

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
                ui.button(team, on_click=pick).props("flat dense").classes(
                    "w-full text-left text-sm"
                )
    input_el.on("input", on_input)


def build_match_button(match: Match, prediction_container):
    btn = ui.button().props("flat").classes(
        "bg-green-50 hover:bg-green-100 text-black border border-green-200 h-full w-full"
    )
    with btn:
        with ui.column().classes("gap-0 items-center w-full"):
            ui.label(f"{match.home_team} vs {match.away_team}").classes(
                "font-semibold text-sm text-center"
            )
            ui.label(
                match.match_date.astimezone(AMSTERDAM).strftime("%d %b %Y %H:%M")
            ).classes("text-xs text-gray-500 text-center")
            if match.stage:
                ui.label(match.stage).classes("text-xs text-gray-400 text-center")
    btn.on_click(lambda _, m=match: select_match(m, prediction_container))


def build_rules_card():
    ui.label("Rules").classes("text-lg font-bold mb-3")
    for pts, label in [
        ("3 pts", "Exact score"),
        ("1 pt",  "Correct winner"),
        ("0 pts", "Wrong prediction"),
    ]:
        with ui.row().classes("w-full items-center py-2 border-b border-gray-100"):
            ui.label(pts).classes("font-bold text-sm w-14 text-green-700")
            ui.label(label).classes("text-sm")

    ui.label("Deadline").classes("font-semibold text-sm mt-4 mb-1")
    ui.label("Predictions lock when the match kicks off.").classes("text-xs text-gray-500")

    ui.label("Tips").classes("font-semibold text-sm mt-3 mb-1")
    ui.label("All times are Amsterdam time (CEST).").classes("text-xs text-gray-500")


def build_finished_matches(current_user):
    finished = get_finished_predictions(current_user)

    with ui.column().classes("flex-1 gap-2"):
        ui.label("✅ Finished matches").classes("text-xl font-bold")

        if not finished:
            ui.label("No finished matches yet.").classes("text-sm text-gray-400")
            return

        for match, prediction in finished:
            pts = prediction.points_earned or 0
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
                ui.label(f"Your pick: {prediction.pred_home_score} – {prediction.pred_away_score}").classes(
                    "text-xs text-gray-500"
                )


def build_my_predictions(current_user):
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
                ui.label(
                    match.match_date.astimezone(AMSTERDAM).strftime("%d %b · %H:%M")
                ).classes("text-xs text-gray-500 mt-1")


def run_search(home_val, away_val, available, finished, upcoming, container):
    """Filter all match lists by search terms and render results."""
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
                    ui.label(
                        f"{m.home_team} vs {m.away_team} · "
                        f"{m.match_date.astimezone(AMSTERDAM).strftime('%d %b %H:%M')}"
                    ).classes("text-sm")

            fin_hits = [(m, p) for m, p in finished if matches_search(m.home_team, m.away_team)]
            if fin_hits:
                found_any = True
                ui.label("Finished").classes("text-sm font-semibold text-gray-500 mt-3 mb-1")
                for m, p in fin_hits:
                    ui.label(
                        f"{m.home_team} vs {m.away_team} · "
                        f"Result {m.home_score}–{m.away_score} · "
                        f"Your pick {p.pred_home_score}–{p.pred_away_score} · "
                        f"{p.points_earned or 0} pts"
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


# ── Prediction form ───────────────────────────────────────────────────────────

def select_match(match: Match, container):
    container.clear()

    with container:
        ui.label(f"{match.home_team} vs {match.away_team}").classes("text-lg font-bold")
        ui.label(
            match.match_date.astimezone(AMSTERDAM).strftime("%d %b %Y %H:%M")
        ).classes("text-xs text-gray-500 mb-2")
        ui.separator()

        with ui.row().classes("items-end justify-center w-full gap-6 mt-4"):
            with ui.column().classes("items-center gap-1"):
                ui.label(match.home_team).classes("text-xs text-gray-500")
                home_num = ui.number(min=0, max=10, value=0).classes("w-20 text-center")

            ui.label("vs").classes("text-lg font-bold pb-1")

            with ui.column().classes("items-center gap-1"):
                ui.label(match.away_team).classes("text-xs text-gray-500")
                away_num = ui.number(min=0, max=10, value=0).classes("w-20 text-center")

        ui.separator().classes("mt-4")

        def on_save():
            # save_prediction(current_user, match, int(home_num.value), int(away_num.value))
            ui.notify("Saved (wire current_user in when ready)")

        ui.button("Save prediction", on_click=on_save).classes(
            "mt-4 w-full bg-blue-500 text-white"
        )