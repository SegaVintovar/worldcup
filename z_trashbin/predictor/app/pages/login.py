"""Login page — shown to unauthenticated users."""
from nicegui import ui
from services.auth import get_login_url


def login_page():
    with ui.column().classes("items-center justify-center min-h-screen w-full"):
        ui.label("⚽ Football Predictor").classes("text-4xl font-bold mb-2")
        ui.label("Predict match scores. Climb the leaderboard.").classes("text-gray-500 mb-8")
        ui.button(
            "Login with 42",
            on_click=lambda: ui.navigate.to(get_login_url())
        ).classes("bg-black text-white px-8 py-3 text-lg rounded")
