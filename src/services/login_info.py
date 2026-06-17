from nicegui import ui
from src.services.database import User, Prediction, SessionLocal


def info_prd(prd: list[Prediction]):
    for p in prd:
        with ui.card():
            with ui.row().style(
                "width: 100%; justify-content: space-between; "
                "padding: 6px 0; border-bottom: 1px solid #eee;"
            ):
                
                    # Match + time (assuming match has datetime or kickoff)
                    ui.label(f"{p.match.home_team} vs {p.match.away_team}") \
                        .style("width: 45%; font-size: 0.95em;")

                    ui.label(f"{p.pred_home_score}:{p.pred_away_score}") \
                        .style("width: 20%; text-align: center;")

                    ui.label(str(p.points_earned)) \
                        .style("width: 15%; text-align: right;")



def login_info(user: User):
    db = SessionLocal()
    prd = db.query(Prediction)\
        .filter(Prediction.user_id == user.id)\
        .order_by(Prediction.id.desc())\
        .limit(5)\
        .all()

    avatar = user.avatar_url or '/assets/image.png'
    with ui.column().style("width: 100%; align-items: center;"):
        with ui.card().style(
            "border-radius: 12px; padding: 20px; width: 100%; height: 50%;"
            "box-shadow: 0 2px 10px rgba(0,0,0,0.08);"
        ):
            with ui.row().style("width: 100%; gap: 30px;"):

                # LEFT SIDE
                with ui.column().style("flex: 1; align-items: center;"):
                    ui.image(avatar).style(
                        "width: 200px; height: 200px; border-radius: 50%; object-fit: cover;"
                    )

                    ui.label(user.login_42).classes("text-xl font-bold mt-2")

                    ui.label(f"Prediction Score: {user.p_score}") \
                        .style("font-size: 1.1em; color: #666;")

                # RIGHT SIDE
                with ui.column().style("flex: 2;"):
                    ui.label("Recent predictions") \
                        .classes("text-xl font-bold mb-2")

                    with ui.column().style(
                        "border: 1px solid #eee; border-radius: 10px; "
                        "padding: 10px; max-height: 250px; overflow-y: auto;"
                    ):
                        if not prd:
                            ui.label("No predictions yet")
                            ui.button("Go to Make Prediction page and predict football matches", on_click=lambda x: ui.navigate.to('/predict'))
                        else:
                            info_prd(prd)

        db.close()