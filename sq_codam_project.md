# sq.codam.nl — Project Structure & Database Models

---

## Project structure

```
sq-codam/
│
├── main.py                  # App entry point, starts NiceGUI
├── .env                     # Secrets: DB URL, API keys, OAuth credentials
├── requirements.txt
│
├── core/
│   ├── __init__.py
│   ├── config.py            # Loads .env variables
│   └── database.py          # SQLAlchemy engine + session factory
│
├── models/
│   ├── __init__.py
│   ├── user.py              # User model
│   ├── match.py             # Match model
│   ├── prediction.py        # Prediction model
│   └── score.py             # UserScore model
│
├── services/
│   ├── __init__.py
│   ├── auth.py              # 42 OAuth flow (login, callback, session)
│   ├── football_api.py      # Fetch fixtures + results from football-data.org
│   └── scheduler.py         # APScheduler jobs (sync matches, trigger scoring)
│
├── pages/
│   ├── __init__.py
│   ├── login.py             # Login page (NiceGUI)
│   ├── fixtures.py          # Fixtures + prediction input page
│   ├── leaderboard.py       # Leaderboard page
│   ├── my_predictions.py    # Personal prediction history
│   └── admin.py             # Admin panel
│
└── static/
    └── logo.png             # Optional assets
```

---

## Database models

### `models/user.py`

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True)
    intra_login   = Column(String, unique=True, nullable=False)  # e.g. "jdoe"
    display_name  = Column(String, nullable=False)
    email         = Column(String, unique=True)
    avatar_url    = Column(String)
    campus_id     = Column(Integer, nullable=False)              # must be 14 (Codam)
    is_admin      = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    predictions   = relationship("Prediction", back_populates="user")
    scores        = relationship("UserScore",  back_populates="user")
```

---

### `models/match.py`

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from core.database import Base

class Match(Base):
    __tablename__ = "matches"

    id              = Column(Integer, primary_key=True)
    api_id          = Column(Integer, unique=True, nullable=False)  # ID from football-data.org
    home_team       = Column(String, nullable=False)
    away_team       = Column(String, nullable=False)
    kickoff_time    = Column(DateTime, nullable=False)
    stage           = Column(String)                  # e.g. "GROUP_STAGE", "QUARTER_FINALS"
    matchday        = Column(Integer)

    # Filled in after the match
    home_score      = Column(Integer, nullable=True)
    away_score      = Column(Integer, nullable=True)
    finished        = Column(Boolean, default=False)

    predictions     = relationship("Prediction", back_populates="match")
    scores          = relationship("UserScore",  back_populates="match")
```

---

### `models/prediction.py`

```python
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime

class Prediction(Base):
    __tablename__ = "predictions"

    id                    = Column(Integer, primary_key=True)
    user_id               = Column(Integer, ForeignKey("users.id"),  nullable=False)
    match_id              = Column(Integer, ForeignKey("matches.id"), nullable=False)
    predicted_home_score  = Column(Integer, nullable=False)
    predicted_away_score  = Column(Integer, nullable=False)
    submitted_at          = Column(DateTime, default=datetime.utcnow)
    updated_at            = Column(DateTime, onupdate=datetime.utcnow)

    # One prediction per user per match — enforced at DB level
    __table_args__ = (UniqueConstraint("user_id", "match_id"),)

    user  = relationship("User",  back_populates="predictions")
    match = relationship("Match", back_populates="predictions")
```

---

### `models/score.py`

```python
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime

class UserScore(Base):
    __tablename__ = "user_scores"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id"),  nullable=False)
    match_id     = Column(Integer, ForeignKey("matches.id"), nullable=False)
    points       = Column(Integer, default=0)        # Points earned for this match
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # One score row per user per match
    __table_args__ = (UniqueConstraint("user_id", "match_id"),)

    user  = relationship("User",  back_populates="scores")
    match = relationship("Match", back_populates="scores")
```

---

### `core/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    """Dependency: yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Creates all tables if they don't exist yet. Call once at startup."""
    from models import user, match, prediction, score  # noqa: import triggers registration
    Base.metadata.create_all(bind=engine)
```

---

### `core/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL:        str   # e.g. postgresql://user:pass@localhost/sq_codam
    FT_CLIENT_ID:        str   # From api.intra.42.fr
    FT_CLIENT_SECRET:    str
    FT_REDIRECT_URI:     str   # e.g. https://sq.codam.nl/auth/callback
    FOOTBALL_API_KEY:    str   # From football-data.org
    SECRET_KEY:          str   # Random string for session signing

    class Config:
        env_file = ".env"

settings = Settings()
```

---

### `.env` (never commit this to git)

```
DATABASE_URL=postgresql://sq_user:yourpassword@localhost/sq_codam
FT_CLIENT_ID=your_42_client_id
FT_CLIENT_SECRET=your_42_client_secret
FT_REDIRECT_URI=https://sq.codam.nl/auth/callback
FOOTBALL_API_KEY=your_football_data_key
SECRET_KEY=a_long_random_string
```

---

## `requirements.txt`

```
nicegui
sqlalchemy
psycopg2-binary       # PostgreSQL driver
pydantic-settings     # .env loader
httpx                 # HTTP client for 42 OAuth + football API
apscheduler           # Scheduled match sync jobs
python-dotenv
```

---

## Setup commands (on the server)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create the PostgreSQL database
sudo -u postgres psql
  CREATE USER sq_user WITH PASSWORD 'yourpassword';
  CREATE DATABASE sq_codam OWNER sq_user;
  \q

# 3. Create all tables (run once)
python -c "from core.database import init_db; init_db()"

# 4. Start the app
python main.py
```

---

## What's next

1. **`services/auth.py`** — implement the 42 OAuth callback
2. **`services/football_api.py`** — fetch UCL fixtures from football-data.org
3. **`services/scheduler.py`** — schedule the sync job hourly
4. **`pages/login.py`** — first NiceGUI page
