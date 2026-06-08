from nicegui import ui
from .header import header


@ui.page("/matches")
def matches():
    header()
    ui.lable("All matches")
