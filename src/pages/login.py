"""Login page — shown to unauthenticated users."""
from nicegui import ui, app
from src.services.auth import get_login_url
import os
from src.assets import theme

from sqlalchemy.orm import Session
from src.services.database import SessionLocal, User


DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"


# def login_page():
#     ui.query('.nicegui-content').style('background-color: #F5EAD8')
#     with ui.column().classes("items-center justify-center min-h-screen w-full"):
#         ui.label("⚽ Football Predictor").classes("text-4xl font-bold mb-2")
#         ui.label("Predict match scores. Climb the leaderboard.").classes("text-gray-500 mb-8")

#         if DEV_MODE:
#             ui.button(
#                 "Login in DEV_MODE",
#                 on_click=dev_login  # ← no parentheses
#             )
#         else:
#             ui.button(
#                 "Login with 42",
#                 on_click=lambda: ui.navigate.to(get_login_url())
#             ).classes("bg-black text-white px-8 py-3 text-lg rounded")


def login_page():
    ui.query('.nicegui-content').style(f'background-color: {theme.BG}')
    with ui.column().classes("items-center justify-center min-h-screen w-full gap-2"):
        with ui.element('div').classes('w-28 h-28 rounded-full overflow-hidden mb-4') \
                .style(f'border: 3px solid {theme.INK};'):
            ui.image('/assets/sidequest_logo.png').classes('w-full h-full object-cover')

        ui.label("Football Predictor").classes("text-4xl mb-1").style(
            f'color: {theme.INK}; font-weight: 600;'
        )
        ui.label("Predict match scores. Climb the leaderboard.").classes("mb-8").style(
            f'color: {theme.INK_MUTED};'
        )

        if DEV_MODE:
            ui.button(
                "Login in DEV_MODE",
                on_click=dev_login  # ← no parentheses
            ).props('unelevated').classes("sq-btn-primary px-8 py-3 text-lg")
        else:
            ui.button(
                "Login with 42",
                on_click=lambda: ui.navigate.to(get_login_url())
            ).props('unelevated').classes("sq-btn-primary px-8 py-3 text-lg")



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