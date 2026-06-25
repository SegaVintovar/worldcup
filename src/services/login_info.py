# from nicegui import ui
# from src.services.database import User, Prediction, SessionLocal


# def info_prd(prd: list[Prediction]):

#     with ui.row().style(
#         "width: 100%; justify-content: space-between; "
#         "border-bottom: 1px solid #eee;"
#     ):
#         with ui.column().style("width: 50%;"):
#             ui.label("Match").classes("text-xl font-bold mt-2")
#         with ui.column().style("width: 25%;"):
#             ui.label("Score").classes("text-xl font-bold mt-2")
#         with ui.column().style("width: 15%;"):
#             ui.label("Points Earned").classes("text-xl font-bold mt-2")

#     for p in prd:
#         with ui.card().style("width: 100%;"):
#             with ui.row().style(
#                 "width: 100%; justify-content: space-between; "
#                 "border-bottom: 1px solid #eee;"
#             ):
#                 with ui.column().style("width: 50%;"):
#                     # Match + time (assuming match has datetime or kickoff)
#                     ui.label(f"{p.match.home_team} vs {p.match.away_team}") \
#                         .style("width: 60%; font-size: 0.95em;")
#                 with ui.column().style("width: 25%;"): 
#                     ui.label(f"{p.pred_home_score}:{p.pred_away_score}") \
#                         .style("width: 20%; text-align: center;")
#                 with ui.column().style("width: 15%;"):
#                     ui.label(str(p.points_earned)) \
#                         .style("width: 15%; text-align: right;")



# def login_info(user: User):
#     db = SessionLocal()
#     try:
#         prd = db.query(Prediction)\
#             .filter(Prediction.user_id == user.id)\
#             .order_by(Prediction.id.desc())\
#             .limit(5)\
#             .all()

#         avatar = user.avatar_url or '/assets/image.png'
#         with ui.column().style("width: 100%; align-items: center;"):
#             with ui.card().style(
#                 "border-radius: 12px; padding: 20px; width: 100%; height: 50%;"
#                 "box-shadow: 0 2px 10px rgba(0,0,0,0.08);"
#             ):
#                 with ui.row().style("width: 100%; gap: 30px;"):

#                     # LEFT SIDE
#                     with ui.column().style("flex: 1; align-items: center;"):
#                         ui.image(avatar).style(
#                             "width: 200px; height: 200px; border-radius: 50%; object-fit: cover;"
#                         )

#                         ui.label(user.login_42).classes("text-xl font-bold mt-2")

#                         ui.label(f"Prediction Score: {user.p_score}") \
#                             .style("font-size: 1.1em; color: #666;")

#                     # RIGHT SIDE
#                     with ui.column().style("flex: 2;"):
#                         ui.label("Recent predictions") \
#                             .classes("text-xl font-bold mb-2")

#                         # with ui.column().style(
#                         #     "border: 1px solid #eee; border-radius: 10px; "
#                         #     "padding: 10px; max-height: 250px; overflow-y: auto;"
#                         # ):
#                         if not prd:
#                             ui.label("No predictions yet")
#                             ui.button("Go to Make Prediction page and predict football matches", on_click=lambda x: ui.navigate.to('/predict'))
#                         else:
#                             info_prd(prd)
#     finally:
#         db.close()


from nicegui import ui
from src.services.database import User, Prediction, SessionLocal
from src.assets import theme


def info_prd(prd: list[Prediction]):

    with ui.row().style(
        f"width: 100%; justify-content: space-between; "
        f"border-bottom: 1px solid {theme.DIVIDER};"
    ):
        with ui.column().style("width: 50%;"):
            ui.label("Match").classes("text-xl mt-2").style(f'color: {theme.INK}; font-weight: 600;')
        with ui.column().style("width: 25%;"):
            ui.label("Score").classes("text-xl mt-2").style(f'color: {theme.INK}; font-weight: 600;')
        with ui.column().style("width: 15%;"):
            ui.label("Points Earned").classes("text-xl mt-2").style(f'color: {theme.INK}; font-weight: 600;')

    for p in prd:
        with ui.card().style(
            f"width: 100%; background-color: {theme.CARD_BG}; "
            f"border: 1px solid {theme.INK}; border-radius: {theme.RADIUS};"
        ):
            with ui.row().style(
                f"width: 100%; justify-content: space-between; "
                f"border-bottom: 1px solid {theme.DIVIDER};"
            ):
                with ui.column().style("width: 50%;"):
                    # Match + time (assuming match has datetime or kickoff)
                    ui.label(f"{p.match.home_team} vs {p.match.away_team}") \
                        .style(f"width: 60%; font-size: 0.95em; color: {theme.INK};")
                with ui.column().style("width: 25%;"):
                    ui.label(f"{p.pred_home_score}:{p.pred_away_score}") \
                        .style(f"width: 20%; text-align: center; color: {theme.INK};")
                with ui.column().style("width: 15%;"):
                    ui.label(str(p.points_earned)) \
                        .style(f"width: 15%; text-align: right; color: {theme.GREEN}; font-weight: 600;")



def login_info(user: User):
    db = SessionLocal()
    try:
        prd = db.query(Prediction)\
            .filter(Prediction.user_id == user.id)\
            .order_by(Prediction.id.desc())\
            .limit(5)\
            .all()

        avatar = user.avatar_url or '/assets/image.png'
        with ui.column().style("width: 100%; align-items: center;"):
            with ui.card().style(
                f"border-radius: {theme.RADIUS}; padding: 20px; width: 100%; height: 50%; "
                f"background-color: {theme.CARD_BG}; border: 1px solid {theme.INK}; "
                f"box-shadow: none;"
            ):
                with ui.row().style("width: 100%; gap: 30px;"):

                    # LEFT SIDE
                    with ui.column().style("flex: 1; align-items: center;"):
                        ui.image(avatar).style(
                            f"width: 200px; height: 200px; border-radius: 50%; object-fit: cover; "
                            f"border: 2px solid {theme.INK};"
                        )

                        ui.label(user.login_42).classes("text-xl mt-2").style(f'color: {theme.INK}; font-weight: 600;')

                        ui.label(f"Prediction Score: {user.p_score}") \
                            .style(f"font-size: 1.1em; color: {theme.INK_MUTED};")

                    # RIGHT SIDE
                    with ui.column().style("flex: 2;"):
                        ui.label("Recent predictions") \
                            .classes("text-xl mb-2").style(f'color: {theme.INK}; font-weight: 600;')

                        if not prd:
                            ui.label("No predictions yet").style(f'color: {theme.INK_MUTED};')
                            ui.button(
                                "Go to Make Prediction page and predict football matches",
                                on_click=lambda x: ui.navigate.to('/predict')
                            ).props('unelevated').classes('sq-btn-primary')
                        else:
                            info_prd(prd)
    finally:
        db.close()
