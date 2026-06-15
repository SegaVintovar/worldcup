"""
services/football_api.py

Fetches World Cup 2026 fixtures and results using openfootball/worldcup.json
"""

import requests
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

OPENFOOTBALL_URL = (
    "https://raw.githubusercontent.com/openfootball/worldcup.json"
    "/master/2026/worldcup.json"
)

# ── Fetch ──────────────────────────────────────────────────────────────────────

def _fetch_openfootball() -> list[dict]:
    try:
        response = requests.get(OPENFOOTBALL_URL, timeout=10)
        response.raise_for_status()
        return response.json().get("matches", [])
    except Exception as e:
        logger.error(f"openfootball fetch failed: {e}")
        return []

# ── Normalize ──────────────────────────────────────────────────────────────────

def _parse_kickoff(date_str: str, time_str: str) -> datetime | None:
    try:
        parts = time_str.split(" ")
        time_clean = parts[0]
        offset_str = parts[1] if len(parts) > 1 else "UTC"
        dt = datetime.strptime(f"{date_str} {time_clean}", "%Y-%m-%d %H:%M")
        offset_hours = 0 if offset_str == "UTC" else int(offset_str.replace("UTC", ""))
        offset = timezone(timedelta(hours=offset_hours))
        return dt.replace(tzinfo=offset).astimezone(timezone.utc)
    except Exception:
        return None

def _compute_winner(home_team, away_team, home_score, away_score):
    if home_score is None or away_score is None:
        return None
    if home_score > away_score:
        return home_team
    if away_score > home_score:
        return away_team
    return "Draw"

def _normalize_openfootball(raw: list[dict]) -> list[dict]:
    matches = []
    for m in raw:
        date = m.get("date", "")
        time = m.get("time", "00:00 UTC")
        home = m.get("team1", "")
        away = m.get("team2", "")

        score = m.get("score")
        home_score = away_score = None
        finished = False

        if score:
            try:
                ft = score.get("ft", [None, None])
                home_score = int(ft[0])
                away_score = int(ft[1])
                finished = True
            except (TypeError, ValueError, IndexError):
                pass

        stage = m.get("round", "")
        phase = "Group Phase" if stage.lower().startswith("matchday") else "Knockout Phase"

        matches.append({
            "source_id":    f"{home}_vs_{away}_{date}".replace(" ", "_").lower(),
            "home_team":    home,
            "away_team":    away,
            "kickoff_time": _parse_kickoff(date, time),
            "stage":        stage,
            "phase":        phase,
            "home_score":   home_score,
            "away_score":   away_score,
            "finished":     finished,
        })
    return matches

# ── Public ─────────────────────────────────────────────────────────────────────

def get_worldcup_matches() -> list[dict]:
    return _normalize_openfootball(_fetch_openfootball())

# ── DB Sync ────────────────────────────────────────────────────────────────────

def sync_matches_to_db(db) -> None:
    from src.services.database import Match

    matches = get_worldcup_matches()
    new_count = updated_count = 0

    for m in matches:
        existing = db.query(Match).filter_by(source_id=m["source_id"]).first()
        winner = _compute_winner(m["home_team"], m["away_team"], m["home_score"], m["away_score"])

        if existing:
            if m["finished"]:
                existing.home_score = m["home_score"]
                existing.away_score = m["away_score"]
                existing.played = True
                existing.winner = winner
                updated_count += 1
        else:
            db.add(Match(
                source_id  = m["source_id"],
                home_team  = m["home_team"],
                away_team  = m["away_team"],
                match_date = m["kickoff_time"],
                stage      = m["stage"],
                phase      = m["phase"],
                home_score = m["home_score"],
                away_score = m["away_score"],
                played     = m["finished"],
                winner     = winner
            ))
            new_count += 1

    db.commit()
    logger.info(f"Sync complete: {new_count} new, {updated_count} updated.")


def update_matches(db) -> None:
    from src.services.database import Match

    external_by_id = {m["source_id"]: m for m in get_worldcup_matches()}
    updated_count = 0

    for match in db.query(Match).all():
        external = external_by_id.get(match.source_id)
        if not external:
            continue

        changed = False
        new_winner = _compute_winner(match.home_team, match.away_team, external["home_score"], external["away_score"])

        if external["finished"] and not match.played:
            match.played = True
            match.home_score = external["home_score"]
            match.away_score = external["away_score"]
            match.winner = new_winner
            changed = True
        elif match.played and (
            match.home_score != external["home_score"]
            or match.away_score != external["away_score"]
        ):
            match.home_score = external["home_score"]
            match.away_score = external["away_score"]
            match.winner = new_winner
            changed = True

        if changed:
            updated_count += 1

    db.commit()
    logger.info(f"Updated {updated_count} matches.")

    