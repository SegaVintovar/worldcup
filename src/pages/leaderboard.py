"""Leaderboard page — shows ranked users by total points."""
from nicegui import ui
from src.services.scoring import calculate_rankings


def leaderboard_page():
    ui.label("🏆 Leaderboard").classes("text-3xl font-bold mb-6")

    rankings = calculate_rankings()
    if not rankings:
        ui.label("No scores yet — predictions will appear here after matches are played.").classes("text-gray-400")
        return

    medals = ["🥇", "🥈", "🥉"]
    for i, entry in enumerate(rankings):
        medal = medals[i] if i < 3 else f"#{i+1}"
        with ui.row().classes("items-center gap-4 mb-3 w-full"):
            ui.label(medal).classes("text-2xl w-8")
            if entry["avatar_url"]:
                ui.image(entry["avatar_url"]).classes("w-10 h-10 rounded-full")
            ui.label(entry["login"]).classes("flex-1 font-medium")
            ui.label(f"{entry['p_score']} pts").classes("font-bold text-blue-600")
