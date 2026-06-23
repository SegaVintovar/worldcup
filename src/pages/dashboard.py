"""Leaderboard page — shows ranked users by total points."""
from nicegui import ui, app
from pathlib import Path
from src.services.match_calender import build_match_calendar
from src.services.login_info import login_info
from src.services.database import User
from src.services.header import header

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
app.add_static_files("/assets", str(ASSETS_DIR))


def dashboard_page(user: User):
    header("/dashboard")
    ui.add_css('''
        .q-message-avatar {
            width: 64px !important;
            height: 64px !important;
            border: 2px solid #444 !important;
        }
    ''')
    ui.query('.nicegui-content').style('background-color: #F5EAD8')
    with ui.column().style('width: 100%'):
        with ui.element('div').classes('p-2').style('width: 100%'):
            ui.label("Dashboard").classes("text-3xl font-bold mb-6")

            with ui.card():
                ui.chat_message(('Welcome to the SideQuest Football Prediction app!\n',
                                'On this page you can check your prediction results.',
                                'Make your predictions for World Cup Knockout-stage!',
                                'Don\'t forget to check your position on the leaderboard.'),
                        name='SQoot',
                        avatar='/assets/owl_prediction_mascot.png')
        login_info(user)
        build_match_calendar()