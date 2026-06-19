from nicegui import ui, app
from pathlib import Path
from zoneinfo import ZoneInfo
from src.services import state

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
app.add_static_files("/assets", str(ASSETS_DIR))

AMSTERDAM = ZoneInfo("Europe/Amsterdam")


def header(active_path: str = "") -> None:
    css = 'text-black'
    # css_p = 'bg-green-600'
    css_predict = css if active_path == "/predict" else ""
    css_leaderboard = css if active_path == "/leaderboard" else ""
    css_dashboard = css if active_path == "/dashboard" else ""

    with ui.header().classes('items-center'):

        with ui.row().classes('items-center w-full'):

            # ── LEFT SIDE (logo + buttons)
            with ui.row().classes('items-center'):
                with ui.element('div').classes('w-12 h-12 rounded-full overflow-hidden bg-transparent'):
                    ui.image('/assets/sidequest_logo.png').classes('w-full h-full object-cover')

                with ui.button_group():
                    ui.button(
                        "Dashboard",
                        on_click=lambda: ui.navigate.to('/dashboard', new_tab=False)
                    ).classes(css_dashboard)

                    ui.button(
                        "Leaderboard",
                        on_click=lambda: ui.navigate.to('/leaderboard', new_tab=False)
                    ).classes(css_leaderboard)

                    ui.button(
                        "Make Prediction",
                        on_click=lambda: ui.navigate.to('/predict', new_tab=False)
                    ).classes(css_predict).props("color=positive")

            # pushes everything to the right
            ui.space()
            ui.button(
                "Logout",
                on_click=lambda: ui.navigate.to("/logout")
            ).classes("ml-auto")
            # ── RIGHT SIDE (last sync)
            if state.LAST_SYNC:
                ui.label(
                    f"🕒 Updated {state.LAST_SYNC.astimezone(AMSTERDAM).strftime('%d %b %H:%M')}"
                ).classes('text-xs text-gray-200')
            else:
                ui.label(
                    "🕒 Updated None"
                ).classes('text-xs text-gray-200')
