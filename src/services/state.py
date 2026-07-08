from datetime import datetime

LAST_SYNC: datetime | None = None


# when set to false (dev-mode), you can make predictions on matches that
# have already been played
PREDICTION_LIMITS = False 

# only show knockout phase matches
KO_ONLY = True

# only show matches of teams where both countries are decided
CONFIRMED_ONLY = True

ADMINS = ["sbonevel", "dev_user", "obirukov", "vsudak"]
