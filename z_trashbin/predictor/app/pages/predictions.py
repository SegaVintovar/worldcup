"""Predictions page — logged-in users submit score predictions."""
from nicegui import ui
from services.database import SessionLocal, Match, Prediction, User


def predictions_page(current_user: User):
    db = SessionLocal()
    try:
        matches = db.query(Match).filter(Match.home_score.is_(None)).all()
        existing = {
            p.match_id: p
            for p in db.query(Prediction).filter_by(user_id=current_user.id).all()
        }
    finally:
        db.close()

    ui.label(f"Hello, {current_user.display_name}!").classes("text-2xl font-bold mb-4")
    ui.label("Submit your predictions for upcoming matches:").classes("text-gray-600 mb-6")

    if not matches:
        ui.label("No upcoming matches yet. Check back soon!").classes("text-gray-400")
        return

    for match in matches:
        pred = existing.get(match.id)
        with ui.card().classes("w-full mb-4 p-4"):
            ui.label(f"{match.home_team}  vs  {match.away_team}").classes("text-lg font-semibold")
            with ui.row().classes("items-center gap-4 mt-2"):
                home_input = ui.number(
                    label=match.home_team, value=pred.predicted_home if pred else 0,
                    min=0, max=20
                ).classes("w-24")
                ui.label("—").classes("text-xl")
                away_input = ui.number(
                    label=match.away_team, value=pred.predicted_away if pred else 0,
                    min=0, max=20
                ).classes("w-24")

                def save(m=match, h=home_input, a=away_input, p=pred):
                    db2 = SessionLocal()
                    try:
                        if p:
                            p.predicted_home = int(h.value)
                            p.predicted_away = int(a.value)
                            db2.merge(p)
                        else:
                            db2.add(Prediction(
                                user_id=current_user.id,
                                match_id=m.id,
                                predicted_home=int(h.value),
                                predicted_away=int(a.value),
                            ))
                        db2.commit()
                        ui.notify("Prediction saved!", color="positive")
                    finally:
                        db2.close()

                ui.button("Save", on_click=save).classes("bg-green-600 text-white px-4 py-2 rounded")
