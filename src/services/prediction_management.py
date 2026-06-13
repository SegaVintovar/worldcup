from src.services.database import SessionLocal, Match, Prediction, User


def get_matches_without_predictions(current_user: User, matches: list[Match]) -> list[Match]:
    db = SessionLocal()
    try:
        available: list[Match] = []
        for match in matches:
            prediction = (
                db.query(Prediction)
                .filter(
                    Prediction.user_id == current_user.id,
                    Prediction.match_id == match.id,
                )
                .first()
            )
            if prediction is None:
                available.append(match)
        return available
    finally:
        db.close()


def get_finished_predictions(current_user: User) -> list[tuple[Match, Prediction]]:
    db = SessionLocal()
    try:
        return (
            db.query(Match, Prediction)
            .join(Prediction, Prediction.match_id == Match.id)
            .filter(
                Prediction.user_id == current_user.id,
                Match.played == True,
            )
            .order_by(Match.match_date.desc())
            .limit(5)
            .all()
        )
    finally:
        db.close()


def get_upcoming_predictions(current_user: User) -> list[tuple[Match, Prediction]]:
    db = SessionLocal()
    try:
        return (
            db.query(Match, Prediction)
            .join(Prediction, Prediction.match_id == Match.id)
            .filter(
                Prediction.user_id == current_user.id,
                Match.played == False,
            )
            .order_by(Match.match_date.asc())
            .limit(5)
            .all()
        )
    finally:
        db.close()


def save_prediction(
    current_user:   User,
    match:          Match,
    home_score:     int,
    away_score:     int,
    winner:         str | None = None,
    ):
    db = SessionLocal()
    try:
        existing = (
            db.query(Prediction)
            .filter(
                Prediction.user_id == current_user.id,
                Prediction.match_id == match.id,
            )
            .first()
        )

        if existing:
            existing.pred_home_score = home_score
            existing.pred_away_score = away_score
            existing.winner = winner
        else:
            pred = Prediction(
                user_id=current_user.id,
                match_id=match.id,
                pred_home_score=home_score,
                pred_away_score=away_score,
                winner=winner,
            )
            db.add(pred)

        db.commit()

    finally:
        db.close()