"""Leaderboard page — shows ranked users by total points."""
from nicegui import ui
from src.services.match_calender import build_match_calendar



def dashboard_page():
    ui.label("Dashboard").classes("text-3xl font-bold mb-6")
    
    build_match_calendar()

