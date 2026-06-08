from nicegui import ui


def header() -> None:
    with ui.header():
        ui.link('Matches',     '/matches')
        ui.link('Leaderboard',  '/leaderboard')
        ui.link('My Predictions',      '/my-predictions')
