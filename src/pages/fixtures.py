from nicegui import ui
from header import layout


@ui.page("/matches")
def matches():
    layout()
    ui.lable("All matches")
    