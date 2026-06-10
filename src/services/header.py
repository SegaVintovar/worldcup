from nicegui import ui


def header(active_path: str = "") -> None:
    # if active_path in "
    css = 'bg-green-600 text-black'
    css_predict = f"{css}" if active_path == "/predict" else ""
    css_leaderboard = f"{css}" if active_path == "/leaderboard" else ""
    css_dashboard = f"{css}" if active_path == "/dashboard" else ""

    with ui.header():
        with ui.button_group():

            ui.button("Dashboard", on_click=lambda: ui.navigate.to('/dashboard', new_tab=False)).classes(css_dashboard)
            # ui.button("Dashboard", on_click=lambda: ui.notify('Swithed to Dashboard'))
            ui.button("Leaderboard", on_click=lambda: ui.navigate.to('/leaderboard', new_tab=False)).classes(css_leaderboard)
            ui.button("My Predictions", on_click=lambda: ui.navigate.to('/predict', new_tab=False)).classes(css_predict)


# .classes('bg-green-600 text-black')