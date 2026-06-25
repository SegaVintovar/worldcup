"""Leaderboard page — shows ranked users by total points."""
from nicegui import ui
from src.services.scoring import calculate_rankings
from src.services.header import header
from src.assets import theme


# def leaderboard_page():
#     header("/leaderboard")
#     ui.query('.nicegui-content').style('background-color: #F5EAD8')
#     ui.label("🏆 Leaderboard").classes("text-3xl font-bold mb-6")

#     rankings = calculate_rankings()
#     if not rankings:
#         ui.label("No scores yet — predictions will appear here after matches are played.").classes("text-gray-400")
#         return

#     medals = ["🥇", "🥈", "🥉"]
#     for i, entry in enumerate(rankings):
#         medal = medals[i] if i < 3 else f"#{i+1}"
#         with ui.card().classes('w-full hover:bg-amber-50 transition-colors duration-150'):
#             with ui.row().classes("items-center gap-4 mb-3 w-full flex-nowrap"):
#                 with ui.column().style("flex: 0 0 10%"):
#                     ui.label(medal).classes("text-2xl w-8")
#                 with ui.column().style("flex: 0 0 20%").classes("items-center gap-2"):
#                     if entry["avatar_url"]:
#                         ui.image(entry["avatar_url"]).classes("w-10 h-10 rounded-full")
#                     ui.label(entry["login"]).classes("flex-1 font-medium")
#                 with ui.column().style("flex: 0 0 70%").classes("items-right"):
#                     ui.label(f"{entry['p_score']} pts").classes("font-bold text-blue-600")


def leaderboard_page():
    header("/leaderboard")
    ui.query('.nicegui-content').style(f'background-color: {theme.BG}')
    
    css1 = ".leaderboard-row { transition: background-color 0.15s ease; cursor: default; }"
    css2 = ".leaderboard-row:hover { background-color: #F0E6D2; }"
    css3 = f".leaderboard-row.top-1 {{ border-left: 4px solid {theme.GOLD} !important; }}"
    css4 = f".leaderboard-row.top-2 {{ border-left: 4px solid #9ca3af !important; }}"
    css5 = f".leaderboard-row.top-3 {{ border-left: 4px solid {theme.BROWN} !important; }}"

    html = "".join(["<style>", css1, css2, css3, css4, css5, "</style>"])
    ui.add_head_html(html)

    ui.label("🏆 Leaderboard").classes("text-3xl mb-6").style(f'color: {theme.INK}; font-weight: 600;')



    with ui.card():
        ui.chat_message(('Here is our leaderboard\n',
                        'Because now we are in testing mode, the leaderboard will'
                        ' be reseted on 21st of June\n'
                        'I hope we will be able to provide prizes for top - 3 places'),
                        name='sq.clubs.codam',
                        stamp='now',
                        avatar='/src/assets/owl_prediction_mascot.png')

    rankings = calculate_rankings()
    if not rankings:
        ui.label("No scores yet — predictions will appear here after matches are played.").classes("text-gray-400")
        return

    medals = ["🥇", "🥈", "🥉"]
    border_classes = ["top-1", "top-2", "top-3"]

    # for i, entry in enumerate(rankings):
    #     medal = medals[i] if i < 3 else f"#{i + 1}"
    #     border = border_classes[i] if i < 3 else ""

    #     with ui.card().classes(f"leaderboard-row {border} w-full mb-1").style("padding: 10px 16px"):
    #         with ui.row().classes("items-center w-full flex-nowrap gap-0"):

    #             # Rank — fixed narrow width
    #             with ui.element("div").style("width: 48px; flex-shrink: 0; text-align: center"):
    #                 ui.label(medal).classes("text-2xl")

    #             # Avatar + login — takes remaining space
    #             with ui.row().classes("items-center gap-3 flex-1"):
    #                 if entry["avatar_url"]:
    #                     ui.image(entry["avatar_url"]).classes("w-10 h-10 rounded-full").style("flex-shrink: 0")
    #                 else:
    #                     ui.element("div").classes("w-10 h-10 rounded-full bg-gray-200").style("flex-shrink: 0")
    #                 ui.label(entry["login"]).classes("font-medium text-base truncate")

    #             # Score — fixed width, right-aligned
    #             with ui.element("div").style("width: 80px; flex-shrink: 0; text-align: right"):
    #                 ui.label(f"{entry['p_score']} pts").classes("font-bold text-blue-600 text-base")

    for i, entry in enumerate(rankings):
            medal = medals[i] if i < 3 else f"#{i + 1}"
            border = border_classes[i] if i < 3 else ""

            with ui.card().classes(f"leaderboard-row {border} w-full mb-1").style(
                f"padding: 10px 16px; background-color: {theme.CARD_BG}; "
                f"border: 1px solid {theme.INK}; border-radius: {theme.RADIUS};"
            ):
                with ui.row().classes("items-center w-full flex-nowrap gap-0"):

                    # Rank — fixed narrow width
                    with ui.element("div").style("width: 48px; flex-shrink: 0; text-align: center"):
                        ui.label(medal).classes("text-2xl")

                    # Avatar + login — takes remaining space
                    with ui.row().classes("items-center gap-3 flex-1"):
                        if entry["avatar_url"]:
                            ui.image(entry["avatar_url"]).classes("w-10 h-10 rounded-full").style(
                                f"flex-shrink: 0; border: 1px solid {theme.INK};"
                            )
                        else:
                            ui.element("div").classes("w-10 h-10 rounded-full").style(
                            f"flex-shrink: 0; background-color: {theme.DIVIDER}; border: 1px solid {theme.INK};"
                        )
                    ui.label(entry["login"]).classes("text-base truncate").style(
                        f"color: {theme.INK}; font-weight: 600;"
                    )

                # Score — fixed width, right-aligned
                with ui.element("div").style("width: 80px; flex-shrink: 0; text-align: right"):
                    ui.label(f"{entry['p_score']} pts").classes("text-base").style(
                        f"color: {theme.GREEN}; font-weight: 700;"
                    )
