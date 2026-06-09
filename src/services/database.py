"""
Database setup using SQLAlchemy.
All models are defined here so every file can import them from one place.
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone

DATABASE_URL = os.environ["DATABASE_URL"]

# Engine = the connection to PostgreSQL
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session = a unit of work; open one per request/action, close when done
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# ── Models ──────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True)
    login_42   = Column(String, unique=True, nullable=False)
    avatar_url = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    p_score    = Column(Integer, default=0)

    predictions = relationship("Prediction", back_populates="user")


class Match(Base):
    __tablename__ = "matches"

    id            = Column(Integer, primary_key=True)
    source_id     = Column(String, unique=True, nullable=False)

    home_team     = Column(String, nullable=False)
    away_team     = Column(String, nullable=False)

    home_score    = Column(Integer, nullable=True)
    away_score    = Column(Integer, nullable=True)

    winner        = Column(String, nullable=True)
    played        = Column(Boolean, default=False)

    match_date    = Column(DateTime)
    stage         = Column(String, nullable=True)

    predictions   = relationship("Prediction", back_populates="match")


class Prediction(Base):
    __tablename__ = "predictions"

    id         = Column(Integer, primary_key=True)

    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    match_id   = Column(Integer, ForeignKey("matches.id"), nullable=False)

    pred_home_score = Column(Integer, nullable=False)
    pred_away_score = Column(Integer, nullable=False)

    points_earned = Column(Integer, default=0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user  = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")


def init_db():
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(bind=engine)
