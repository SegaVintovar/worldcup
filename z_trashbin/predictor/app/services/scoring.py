"""
Prediction scoring logic.

Scoring rules (adjust to your taste):
- Exact score:          5 points
- Correct goal diff:    3 points  (e.g. predicted 2-0, actual 3-1)
- Correct winner only:  1 point
- Wrong:                0 points
"""
from services.database import SessionLocal, Prediction, Match


def score_prediction(predicted_home: int, predicted_away: int,
                     actual_home: int, actual_away: int) -> int:
    if predicted_home == actual_home and predicted_away == actual_away:
        return 5
    if (predicted_home - predicted_away) == (actual_home - actual_away):
        return 3
    pred_winner = _winner(predicted_home, predicted_away)
    real_winner = _winner(actual_home, actual_away)
    if pred_winner == real_winner:
        return 1
    return 0


def _winner(home: int, away: int) -> str:
    if home > away:   return "home"
    if away > home:   return "away"
    return "draw"


def calculate_rankings() -> list[dict]:
    """
    Returns a list of {login, display_name, avatar_url, total_points}
    sorted by total_points descending.
    """
    db = SessionLocal()
    try:
        predictions = (
            db.query(Prediction)
            .join(Prediction.match)
            .filter(Match.home_score.isnot(None))  # only scored matches
            .all()
        )
        totals: dict[int, dict] = {}
        for p in predictions:
            uid = p.user_id
            if uid not in totals:
                totals[uid] = {
                    "login":        p.user.login_42,
                    "display_name": p.user.display_name,
                    "avatar_url":   p.user.avatar_url,
                    "total_points": 0,
                }
            totals[uid]["total_points"] += p.points_earned

        return sorted(totals.values(), key=lambda x: x["total_points"], reverse=True)
    finally:
        db.close()
