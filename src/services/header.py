from nicegui import ui, app
from pathlib import Path

# app.add_static_files('/assets', 'src/assets')
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
app.add_static_files("/assets", str(ASSETS_DIR))


def header(active_path: str = "") -> None:
    css = 'bg-green-600 text-black'
    css_predict = css if active_path == "/predict" else ""
    css_leaderboard = css if active_path == "/leaderboard" else ""
    css_dashboard = css if active_path == "/dashboard" else ""

    with ui.header().classes('items-center'):
        with ui.row():
            ui.image('/assets/sidequest_logo.png').classes('w-12 h-12 object-contain shrink-0')
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
                    "My Predictions",
                    on_click=lambda: ui.navigate.to('/predict', new_tab=False)
                ).classes(css_predict)
