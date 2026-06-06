from nicegui import ui

# ui.page()
ui.label("Make your prediction")
with ui.row():
    home_score = ui.select(list(range(0, 25)), value=0, label='Home')
    ui.label('vs').classes('self-center text-xl')
    away_score = ui.select(list(range(0, 25)), value=0, label='Away')

ui.button('Submit', on_click=lambda: print(home_score.value, away_score.value))
ui.run()