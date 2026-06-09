"""
main.py — application entry point.

NiceGUI works differently from Flask:
- @ui.page decorators define routes
- NiceGUI runs its own FastAPI server internally
- We attach extra routes (like the OAuth callback) directly to that FastAPI app
"""
import os
from nicegui import ui, app
from fastapi import Request
from fastapi.responses import RedirectResponse

from services.database import init_db, SessionLocal, User
from services.auth import exchange_code_for_user
from pages.login import login_page
from pages.predictions import predictions_page
from pages.leaderboard import leaderboard_page


# ── Startup ──────────────────────────────────────────────────────────────────

@app.on_startup
async def startup():
    """Runs once when the server starts."""
    init_db()
    print("Database tables ready.")


# ── Session helper ────────────────────────────────────────────────────────────

def get_current_user() -> User | None:
    """
    NiceGUI stores per-browser state in app.storage.user (a dict).
    We store the DB user id there after login.
    """
    user_id = app.storage.user.get("user_id")
    if not user_id:
        return None
    db = SessionLocal()
    try:
        return db.query(User).filter_by(id=user_id).first()
    finally:
        db.close()


# ── OAuth callback — FastAPI route (not a NiceGUI page) ──────────────────────

@app.get("/auth/callback")
async def oauth_callback(request: Request):
    """
    42 redirects here after the user approves login.
    We exchange the code, upsert the user, and set the session.
    """
    code = request.query_params.get("code")
    if not code:
        return RedirectResponse("/")

    profile = await exchange_code_for_user(code)

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(login_42=profile["login"]).first()
        if not user:
            user = User(
            login_42=profile["login"],
            avatar_url=profile.get("image", {}).get("link"),
            )
            db.add(user)
        else:
            # Update avatar in case it changed
            user.avatar_url = profile.get("image", {}).get("link")
        db.commit()
        db.refresh(user)

        # Store user id in session (NiceGUI handles cookie signing)
        request.session["user_id"] = user.id

    finally:
        db.close()

    return RedirectResponse("/predict")


# ── NiceGUI pages ─────────────────────────────────────────────────────────────

@ui.page("/")
def index():
    user = get_current_user()
    if user:
        ui.navigate.to("/predict")
    else:
        login_page()


@ui.page("/predict")
def predict():
    user = get_current_user()
    if not user:
        ui.navigate.to("/")
        return
    with ui.column().classes("max-w-2xl mx-auto p-6"):
        with ui.row().classes("w-full justify-between items-center mb-6"):
            ui.link("🏆 Leaderboard", "/leaderboard").classes("text-blue-600")
            ui.button("Logout", on_click=lambda: (
                app.storage.user.clear(),
                ui.navigate.to("/")
            )).classes("text-sm text-gray-500")
        predictions_page(user)


@ui.page("/leaderboard")
def leaderboard():
    with ui.column().classes("max-w-2xl mx-auto p-6"):
        ui.link("← Back to predictions", "/predict").classes("text-blue-600 mb-4")
        leaderboard_page()


# ── Run ───────────────────────────────────────────────────────────────────────

ui.run(
    host="0.0.0.0",
    port=8080,
    title="Football Predictor",
    favicon="⚽",
    # storage_secret is used to sign session cookies — must be set in production
    storage_secret=os.environ.get("APP_SECRET_KEY", "dev-secret"),
    # Reload only in development; gunicorn handles this in production
    reload=False,
)
