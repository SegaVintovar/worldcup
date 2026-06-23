from datetime import datetime

LAST_SYNC: datetime | None = None


# when set to false (dev-mode), you can make predictions on matches that
# have already been played
PREDICTION_LIMITS = True 