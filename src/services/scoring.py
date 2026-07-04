"""
Prediction scoring logic.

Scoring rules (adjust to your taste):
- Exact score:          5 points
- Correct goal diff:    3 points  (e.g. predicted 2-0, actual 3-1)
- Correct winner only:  1 point
- Wrong:                0 points
"""
from src.services.database import SessionLocal, Prediction, Match, User


def score_prediction(predicted_home: int, predicted_away: int,
                     pred_winner,
                     actual_home: int, actual_away: int,
                     actual_winner) -> int:

    # exact score
    if (
        predicted_home == actual_home and predicted_away == actual_away):

        if pred_winner and pred_winner == actual_winner:
            return 3
        return 3
    if pred_winner and pred_winner == actual_winner:
        return 1
    # correct outcome
    if (
        winner(predicted_home, predicted_away)
        == winner(actual_home, actual_away)
    ):
        return 1

    return 0

# bullshit winner, lol
def winner(home: int, away: int) -> str:
    if home > away:
        return "home"
    if away > home:
        return "away"
    return "draw"

def update_prediction_scores() -> None:
    db = SessionLocal()

    try:
        finished_matches = (
            db.query(Match)
            .filter(Match.played == True)
            .all()
        )

        for match in finished_matches:

            for prediction in match.predictions:

                prediction.points_earned = score_prediction(
                    prediction.pred_home_score,
                    prediction.pred_away_score,
                    prediction.winner,
                    match.home_score,
                    match.away_score,
                    match.winner
                )

        db.commit()

    finally:
        db.close()

def update_user_scores() -> None:
    db = SessionLocal()

    try:
        users = db.query(User).all()

        for user in users:
            user.p_score = sum(
                prediction.points_earned
                for prediction in user.predictions
            )

        db.commit()

    finally:
        db.close()

def calculate_rankings() -> list[dict]:
    db = SessionLocal()

    try:
        users = (
            db.query(User)
            .order_by(User.p_score.desc())
            .all()
        )

        return [
            {
                "login": user.login_42,
                "avatar_url": user.avatar_url,
                "p_score": user.p_score,
            }
            for user in users
        ]

    finally:
        db.close()