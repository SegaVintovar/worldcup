import os
from nicegui import ui, app
from fastapi import Request
from fastapi.responses import RedirectResponse

# pages
from src.pages.login import login_page
from src.pages.predictions import predictions_page
from src.pages.leaderboard import leaderboard_page
from src.pages.dashboard import dashboard_page

# services
from src.services.database import init_db, SessionLocal, User, Match
from src.services.auth import exchange_code_for_user

# outsourced
from src.results.football_api import sync_matches_to_db, update_matches


DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"


@app.on_startup
async def startup():
    print("🚀 App starting up...")
    init_db()

    db = SessionLocal()
    try:
        match_count = db.query(Match).count()
        print(f"📊 Matches in DB: {match_count}")

        if match_count == 0:
            print("⚽ No matches found, syncing from API...")
            sync_matches_to_db(db)
            print(f"✅ Sync complete. Now {db.query(Match).count()} matches in DB.")
        else:
            print("🔄 Updating match results...")
            update_matches(db)
            print("✅ Match results updated.")

    except Exception as e:
        print("❌ Startup sync failed!")
        import traceback
        traceback.print_exc()
    finally:
        db.close()




def get_current_user() -> User | None:
    user_id = app.storage.user.get("user_id")
    if not user_id:
        return None
    db = SessionLocal()
    try:
        return db.query(User).filter_by(id=user_id).first()
    finally:
        db.close()

# @app.get("/auth/callback")
# async def oauth_callback(request: Request):
#     code = request.query_params.get("code")
#     if not code:
#         return RedirectResponse("/")
#     profile = await exchange_code_for_user(code)
#     db = SessionLocal()
#     try:
#         user = db.query(User).filter_by(login_42=profile["login"]).first()
#         if not user:
#             user = User(
#                 login_42=profile["login"],
#                 avatar_url=profile.get("image", {}).get("link"),
#             )
#             db.add(user)
#         else:
#             user.avatar_url = profile.get("image", {}).get("link")
#         db.commit()
#         db.refresh(user)
#         app.storage.user["user_id"] = user.id
#     finally:
#         db.close()
#     return RedirectResponse("/predict")

@ui.page("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        ui.navigate.to("/")
    print("Dashboard route hit!")
    dashboard_page()

@ui.page("/")
def index():
    user = get_current_user()
    if user:
        ui.navigate.to("/dashboard")
    else:
        login_page()

@ui.page("/predict")
def predict():
    user = get_current_user()
    if not user:
        ui.navigate.to("/")

    predictions_page(user)

@ui.page("/leaderboard")
def leaderboard():
    with ui.column().classes("max-w-2xl mx-auto p-6"):
        ui.link("← Back to predictions", "/predict").classes("text-blue-600 mb-4")
        leaderboard_page()

ui.run(
    host="0.0.0.0",
    port=8080,
    title="Football Predictor",
    favicon="⚽",
    storage_secret=os.environ.get("APP_SECRET_KEY", "dev-secret"),
    reload=False,
    on_air=True
)