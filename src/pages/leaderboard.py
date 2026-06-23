"""Leaderboard page — shows ranked users by total points."""
from nicegui import ui, app
from src.services.scoring import calculate_rankings
from src.services.header import header
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
app.add_static_files("/assets", str(ASSETS_DIR))

def leaderboard_page():
    header("/leaderboard")

    ui.query('.nicegui-content').style('background-color: #F5EAD8')

    # Inject hover CSS once — Tailwind hover: doesn't work reliably on ui.card()
    ui.add_head_html("""
    <style>
        .leaderboard-row { transition: background-color 0.15s ease; cursor: default; }
        .leaderboard-row:hover { background-color: #fef3c7; }  /* amber-100 */
        .leaderboard-row.top-1 { border-left: 4px solid #f59e0b; }
        .leaderboard-row.top-2 { border-left: 4px solid #9ca3af; }
        .leaderboard-row.top-3 { border-left: 4px solid #b45309; }
    </style>
    """)

    ui.label("🏆 Leaderboard").classes("text-3xl font-bold mb-6")
    ui.add_css('''
        .q-message-avatar {
            width: 64px !important;
            height: 64px !important;
            border: 2px solid #444 !important;
        }
    ''')
    with ui.card():
        ui.chat_message(('Checkout our leaderboard!\n',
                        '#1 Will get a prize...'),
                        name='SQoot',
                        avatar='/assets/owl_prediction_mascot.png')

    rankings = calculate_rankings()
    if not rankings:
        ui.label("No scores yet — predictions will appear here after matches are played.").classes("text-gray-400")
        return

    medals = ["🥇", "🥈", "🥉"]
    border_classes = ["top-1", "top-2", "top-3"]

    for i, entry in enumerate(rankings):
        medal = medals[i] if i < 3 else f"#{i + 1}"
        border = border_classes[i] if i < 3 else ""

        with ui.card().classes(f"leaderboard-row {border} w-full mb-1").style("padding: 10px 16px"):
            with ui.row().classes("items-center w-full flex-nowrap gap-0"):

                # Rank — fixed narrow width
                with ui.element("div").style("width: 48px; flex-shrink: 0; text-align: center"):
                    ui.label(medal).classes("text-2xl")

                # Avatar + login — takes remaining space
                with ui.row().classes("items-center gap-3 flex-1"):
                    if entry["avatar_url"]:
                        ui.image(entry["avatar_url"]).classes("w-10 h-10 rounded-full").style("flex-shrink: 0")
                    else:
                        ui.element("div").classes("w-10 h-10 rounded-full bg-gray-200").style("flex-shrink: 0")
                    ui.label(entry["login"]).classes("font-medium text-base truncate")

                # Score — fixed width, right-aligned
                with ui.element("div").style("width: 80px; flex-shrink: 0; text-align: right"):
                    ui.label(f"{entry['p_score']} pts").classes("font-bold text-blue-600 text-base")