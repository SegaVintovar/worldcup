"""Login page — shown to unauthenticated users."""
from nicegui import ui
from src.services.auth import get_login_url
import os

DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"


def login_page():
    with ui.column().classes("items-center justify-center min-h-screen w-full"):
        ui.label("⚽ Football Predictor").classes("text-4xl font-bold mb-2")
        ui.label("Predict match scores. Climb the leaderboard.").classes("text-gray-500 mb-8")
        if DEV_MODE:
            ui.button(
                "Login in DEV_MODE",
                on_click=lambda: ui.navigate.to("/dashboard", new_tab=False)
            )

        else:
            ui.button(
            "Login with 42",
            on_click=lambda: ui.navigate.to(get_login_url())
            ).classes("bg-black text-white px-8 py-3 text-lg rounded")

