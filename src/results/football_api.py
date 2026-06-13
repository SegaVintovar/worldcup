"""
services/football_api.py

Fetches World Cup 2026 fixtures and results using two free sources:
  - openfootball/worldcup.json  → fixtures (structure, dates, teams)
  - TheSportsDB                 → results (scores after matches finish)

No API key required for either source.
"""

import requests
import logging
from datetime import datetime, timezone, timedelta


logger = logging.getLogger(__name__)

# ── Sources ────────────────────────────────────────────────────────────────────

OPENFOOTBALL_URL = (
    "https://raw.githubusercontent.com/openfootball/worldcup.json"
    "/master/2026/worldcup.json"
)

THESPORTSDB_URL = "https://www.thesportsdb.com/api/v1/json/1/eventsseason.php"
THESPORTSDB_LEAGUE_ID = "4429"   # FIFA World Cup on TheSportsDB

# ── Fetch raw data ─────────────────────────────────────────────────────────────

def _fetch_openfootball() -> list[dict]:
    """Returns list of raw match dicts from openfootball."""
    try:
        response = requests.get(OPENFOOTBALL_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("matches", [])
    except Exception as e:
        logger.error(f"openfootball fetch failed: {e}")
        return []


def _fetch_thesportsdb() -> list[dict]:
    """Returns list of raw event dicts from TheSportsDB."""
    try:
        response = requests.get(
            THESPORTSDB_URL,
            params={"id": THESPORTSDB_LEAGUE_ID, "s": "2026"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("events") or []
    except Exception as e:
        logger.error(f"TheSportsDB fetch failed: {e}")
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


def _normalize_thesportsdb(raw: list[dict]) -> dict[str, dict]:
    results = {}
    for e in raw:
        home = e.get("strHomeTeam", "")
        away = e.get("strAwayTeam", "")
        date = e.get("dateEvent", "")
        home_score = e.get("intHomeScore")
        away_score = e.get("intAwayScore")

        if home_score is None or away_score is None:
            continue

        key = f"{home}_vs_{away}_{date}".replace(" ", "_").lower()
        results[key] = {
            "home_score": int(home_score),
            "away_score": int(away_score),
            "finished":   True,
        }
    return results


# ── Merge ──────────────────────────────────────────────────────────────────────

def get_worldcup_matches() -> list[dict]:
    """
    Main function. Returns a merged list of all World Cup 2026 matches.

    Strategy:
      1. Use openfootball as the base (fixtures + basic scores)
      2. Overlay TheSportsDB scores where available (usually faster/more reliable)
    """
    logger.info("Fetching World Cup 2026 fixtures from openfootball...")
    matches = _normalize_openfootball(_fetch_openfootball())

    logger.info("Fetching results from TheSportsDB...")
    sportsdb_results = _normalize_thesportsdb(_fetch_thesportsdb())

    for match in matches:
        if match["source_id"] in sportsdb_results:
            match.update(sportsdb_results[match["source_id"]])
            logger.debug(f"Score updated from TheSportsDB: {match['source_id']}")

    logger.info(f"Total matches loaded: {len(matches)}")
    return matches


# ── DB Sync ────────────────────────────────────────────────────────────────────

def sync_matches_to_db(db) -> None:
    from src.services.database import Match

    matches = get_worldcup_matches()
    new_count = updated_count = 0

    for m in matches:
        existing = db.query(Match).filter_by(source_id=m["source_id"]).first()

        if existing:
            if m["finished"] and not existing.played:
                existing.home_score = m["home_score"]
                existing.away_score = m["away_score"]
                existing.played = True
                existing.winner = (
                    existing.home_team if existing.home_score > existing.away_score else
                    existing.away_team if existing.away_score > existing.home_score else
                    "Draw"
                )
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
            ))
            new_count += 1

    db.commit()
    logger.info(f"Sync complete: {new_count} new, {updated_count} updated.")


def update_matches(db) -> None:
    """
    Update existing matches from external sources.
    Does NOT create new fixtures.
    """
    from src.services.database import Match

    external_by_id = {m["source_id"]: m for m in get_worldcup_matches()}
    updated_count = 0

    for match in db.query(Match).all():
        external = external_by_id.get(match.source_id)
        if not external:
            continue

        changed = False

        if external["finished"] and not match.played:
            match.played = True
            match.home_score = external["home_score"]
            match.away_score = external["away_score"]
            match.winner = (
                match.home_team if match.home_score > match.away_score else
                match.away_team if match.away_score > match.home_score else
                "Draw"
            )
            changed = True

        elif match.played and (
            match.home_score != external["home_score"]
            or match.away_score != external["away_score"]
        ):
            match.home_score = external["home_score"]
            match.away_score = external["away_score"]
            # Recalculate winner on score correction
            match.winner = (
                match.home_team if match.home_score > match.away_score else
                match.away_team if match.away_score > match.home_score else
                "Draw"
            )
            changed = True

        if changed:
            updated_count += 1

    db.commit()
    logger.info(f"Updated {updated_count} matches.")


