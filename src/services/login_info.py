

from nicegui import ui
from src.services.database import User, Prediction, SessionLocal


def info_prd(prd: list[Prediction]):
    text_style: str = 'text-align: center; width: 33.3%; font-size: 1em;'
    for p in prd:
        with ui.row().style("display: flex; width: 100%; justify-content: space-between; flex-wrap: nowrap"):
            ui.label(f"{p.match.home_team}-{p.match.away_team}").style(text_style)
            ui.label(f"{p.pred_home_score}:{p.pred_away_score}").style(text_style)
            ui.label(p.points_earned).style(text_style)


def login_info(user: User):
    ava: str

    db = SessionLocal()
    prd = db.query(Prediction).filter(Prediction.user_id == user.id).all()
    if user.avatar_url:
        ava = user.avatar_url
    else:
        ava = '/assets/image.png'
    with ui.row().style("width: 100%; justify-content: center; border: 1px;"):
        with ui.column().classes('p-3 items-center justify-center'):
            with ui.card():
                with ui.column().classes('items-center gap-4 p-4'):
                    with ui.element('div').style('width: 15em; height: 15em; overflow: hidden; border-radius: 50%;'):
                        ui.image(ava).style('width: 100%; height: 100%; object-fit: cover;')
                    ui.label(f"Username: {user.login_42}").classes('font-semibold text-2xl text-center')
                
                # with ui.element('div').classes('p-3 items-center justify-center'):
                #     ui.image(ava).classes('mx-auto rounded-full object-cover').style('width: 15em; height: 15em')
                # ui.label(f"Username: {user.login_42}").classes('w-full h-full font-semibold text-2xl m-20 leading-tight')
        with ui.column():
            ui.label("Predictions").classes("text-3xl h-full font-bold mb-1 justify-center").style("padding-top: 1rem;")
            with ui.row().style("padding: 1.3em; display: flex; width: 100%; justify-content: space-between; flex-wrap: nowrap;"):
                ui.label("Matches").style("font-size: 1.4em; font-weight: bold;")
                ui.label("Score").style("font-size: 1.4em; font-weight: bold;")
                ui.label("Point Earned").style("font-size: 1.4em; font-weight: bold;")
            with ui.element('div').style(
                    'width: 100%; height: 66.66%; overflow-y: auto; border: 1px solid black; padding: 10px; border-radius: 10px;'):
                if prd == []:
                    ui.label("No Predictions").style('font-size: 1.4em; text-align: center;')
                else:
                    info_prd(prd)
    db.close()


