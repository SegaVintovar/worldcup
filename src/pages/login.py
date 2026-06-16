"""Login page — shown to unauthenticated users."""
from nicegui import ui, app
from src.services.auth import get_login_url
import os

from sqlalchemy.orm import Session
from src.services.database import SessionLocal, User


DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"


def login_page():
    ui.query('.nicegui-content').style('background-color: #F5EAD8')
    with ui.column().classes("items-center justify-center min-h-screen w-full"):
        ui.label("⚽ Football Predictor").classes("text-4xl font-bold mb-2")
        ui.label("Predict match scores. Climb the leaderboard.").classes("text-gray-500 mb-8")

        if DEV_MODE:
            ui.button(
                "Login in DEV_MODE",
                on_click=dev_login  # ← no parentheses
            )
        else:
            ui.button(
                "Login with 42",
                on_click=lambda: ui.navigate.to(get_login_url())
            ).classes("bg-black text-white px-8 py-3 text-lg rounded")


def dev_login():
    user = get_or_create_user(
        login_42="dev_user",
        avatar_url=None
    )
    app.storage.user["user_id"] = user.id  # ← this was missing
    ui.navigate.to("/dashboard")


def get_or_create_user(login_42: str, avatar_url: str | None = None) -> User:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.login_42 == login_42).first()
        if user:
            return user

        user = User(
            login_42=login_42,
            avatar_url=avatar_url,
            p_score=0,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()