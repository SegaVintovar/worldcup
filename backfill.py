"""
One-off script: backfill the `winner` column on `predictions` for rows
where it is NULL, based on the predicted score.

Logic mirrors save_prediction() in src/services/prediction_search.py:
    - pred_home_score > pred_away_score  -> winner = match.home_team
    - pred_away_score > pred_home_score  -> winner = match.away_team
    - draw (pred_home_score == pred_away_score) -> left as None
      (matches existing app behavior: draws only get a winner if the
      user explicitly picked one in a Knockout Phase prediction, which
      would already be set and therefore not NULL)

Usage:
    export DATABASE_URL=postgresql://user:pass@host:port/dbname
    python backfill_prediction_winners.py            # dry run, just prints
    python backfill_prediction_winners.py --commit    # actually writes changes
"""
import sys
from src.services.database import SessionLocal, Prediction, Match


def backfill(dry_run: bool = True) -> None:
    db = SessionLocal()
    try:
        rows = (
            db.query(Prediction, Match)
            .join(Match, Prediction.match_id == Match.id)
            .filter(Prediction.winner.is_(None))
            .all()
        )

        print(f"Found {len(rows)} prediction(s) with NULL winner.\n")

        updated = 0
        skipped_draws = 0

        for prediction, match in rows:
            if prediction.pred_home_score > prediction.pred_away_score:
                new_winner = match.home_team
            elif prediction.pred_away_score > prediction.pred_home_score:
                new_winner = match.away_team
            else:
                # predicted draw, nothing to fill in
                skipped_draws += 1
                continue

            print(
                f"  prediction #{prediction.id} "
                f"({match.home_team} vs {match.away_team}, "
                f"pick {prediction.pred_home_score}-{prediction.pred_away_score}) "
                f"-> winner = {new_winner}"
            )

            if not dry_run:
                prediction.winner = new_winner

            updated += 1

        if not dry_run:
            db.commit()
            print(f"\nCommitted. Updated {updated} row(s). Skipped {skipped_draws} predicted draw(s).")
        else:
            print(f"\nDry run only, no changes written. Would update {updated} row(s). "
                  f"Skipped {skipped_draws} predicted draw(s).")
            print("Re-run with --commit to apply.")

    finally:
        db.close()


if __name__ == "__main__":
    commit = "--commit" in sys.argv
    backfill(dry_run=not commit)