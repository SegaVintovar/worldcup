import os
from nicegui import ui, app
from fastapi import Request
from fastapi.responses import RedirectResponse

from services.database import init_db, SessionLocal, User
from services.auth import exchange_code_for_user
from pages.login import login_page
from pages.predictions import predictions_page
from pages.leaderboard import leaderboard_page

DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"


# ── Startup ──────────────────────────────────────────────────────────────────

@app.on_startup
async def startup():
    init_db()
    print("Database tables ready.")

    if DEV_MODE:
        db = SessionLocal()
        try:
            dummy = db.query(User).filter_by(login_42="dev_user").first()

            if not dummy:
                dummy = User(
                    login_42="dev_user",
                    avatar_url=None,
                )
                db.add(dummy)
                db.commit()

                print("Dev dummy user created.")
        finally:
            db.close()

# ── Session helper ────────────────────────────────────────────────────────────

def get_current_user() -> User | None:
    user_id = app.storage.user.get("user_id")
    if not user_id:
        return None
    db = SessionLocal()
    try:
        return db.query(User).filter_by(id=user_id).first()
    finally:
        db.close()


# ── Dev login route (DEV_MODE only) ──────────────────────────────────────────

@app.get("/dev-login")
async def dev_login():
    """Instantly log in as the dummy user — only works when DEV_MODE=true."""
    if not DEV_MODE:
        return RedirectResponse("/")
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(login_42="dev_user").first()
        if user:
            # We can't set app.storage here (it's request-scoped in NiceGUI)
            # so we pass the user_id as a query param and set it in the page
            return RedirectResponse(f"/dev-login-page?uid={user.id}")
    finally:
        db.close()
    return RedirectResponse("/")


@ui.page("/dev-login-page")
def dev_login_page(uid: int):
    """Sets the session and redirects — NiceGUI storage only works inside ui.page."""
    if not DEV_MODE:
        ui.navigate.to("/")
        return
    app.storage.user["user_id"] = uid
    ui.navigate.to("/predict")


# ── OAuth callback ────────────────────────────────────────────────────────────

@app.get("/auth/callback")
async def oauth_callback(request: Request):
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
            user.avatar_url = profile.get("image", {}).get("link")
        db.commit()
        db.refresh(user)
        app.storage.user["user_id"] = user.id
    finally:
        db.close()

    return RedirectResponse("/predict")


# ── Pages ─────────────────────────────────────────────────────────────────────

@ui.page("/")
def index():
    if DEV_MODE:
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(login_42="dev_user").first()
            if user:
                app.storage.user["user_id"] = user.id
                ui.navigate.to("/predict")
                return
        finally:
            db.close()

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
            if DEV_MODE:
                ui.label("⚠️ DEV MODE").classes("text-xs text-orange-400")
            else:
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
    storage_secret=os.environ.get("APP_SECRET_KEY", "dev-secret"),
    reload=False,
)