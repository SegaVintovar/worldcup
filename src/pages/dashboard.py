"""Leaderboard page — shows ranked users by total points."""
from nicegui import ui
from src.services.match_calender import build_match_calendar
from src.services.login_info import login_info
from src.services.database import User
from src.services.header import header



def dashboard_page(user: User):
    header("/dashboard")
    ui.query('.nicegui-content').style('background-color: #F5EAD8')
    with ui.column().style('width: 100%'):
        with ui.element('div').classes('p-2').style('width: 100%'):
            ui.label("Dashboard").classes("text-3xl font-bold mb-6")
            ui.chat_message(('Welcom in Football Predictor app!\n',
                            'On this page you can check your prediction results'),
                    name='sq.clubs.codam',
                    stamp='now',
                    avatar='https://robohash.org/ui')
        login_info(user)
        build_match_calendar()

