from nicegui import ui


def header(active_path: str = "") -> None:
    # if active_path in "
    with ui.header():
        with ui.button_group():
        
            ui.button("Dashboard", on_click=lambda: ui.link('Dashboard', '/dashboard')).classes('bg-blue-600 text-white')
            # ui.button("Dashboard", on_click=lambda: ui.notify('Swithed to Dashboard'))
            ui.button("Leaderboard", on_click=lambda: ui.link('Leaderboard', '/leaderboard')).classes('bg-blue-600 text-white')
            ui.button("My Predictions", on_click=lambda: ui.navigate.to('/predicts'))
