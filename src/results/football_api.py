"""
services/football_api.py

Fetches World Cup 2026 fixtures and results using two free sources:
  - openfootball/worldcup.json  → fixtures (structure, dates, teams)
  - TheSportsDB                 → results (scores after matches finish)

No API key required for either source.
"""

import requests
import logging
from datetime import datetime, timezone

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
    """
    Parses openfootball date + time into a UTC-aware datetime.
    Time strings look like '13:00 UTC-6' or '20:00 UTC'.
    """
    try:
        # Strip timezone label — openfootball times are local to venue,
        # we store as-is and note the offset for display purposes.
        time_clean = time_str.split(" ")[0]  # e.g. '13:00'
        dt = datetime.strptime(f"{date_str} {time_clean}", "%Y-%m-%d %H:%M")
        return dt.replace(tzinfo=timezone.utc)  # treat as UTC for now
    except Exception:
        return None


def _normalize_openfootball(raw: list[dict]) -> list[dict]:
    """
    Converts openfootball matches into our internal format:
    {
        source_id:   str,   # unique key: "team1_vs_team2_date"
        home_team:   str,
        away_team:   str,
        kickoff_time: datetime | None,
        stage:       str,
        home_score:  int | None,
        away_score:  int | None,
        finished:    bool,
    }
    """
    matches = []
    for m in raw:
        date = m.get("date", "")
        time = m.get("time", "00:00 UTC")
        home = m.get("team1", "")
        away = m.get("team2", "")

        score = m.get("score")  # present only after match ends
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

        matches.append({
            "source_id":    f"{home}_vs_{away}_{date}".replace(" ", "_").lower(),
            "home_team":    home,
            "away_team":    away,
            "kickoff_time": _parse_kickoff(date, time),
            "stage":        m.get("round", ""),
            "home_score":   home_score,
            "away_score":   away_score,
            "finished":     finished,
        })
    return matches


def _normalize_thesportsdb(raw: list[dict]) -> dict[str, dict]:
    """
    Returns a dict keyed by 'home_vs_away_date' for fast lookup.
    Only includes finished matches (intHomeScore is not None).
    """
    results = {}
    for e in raw:
        home = e.get("strHomeTeam", "")
        away = e.get("strAwayTeam", "")
        date = e.get("dateEvent", "")
        home_score = e.get("intHomeScore")
        away_score = e.get("intAwayScore")

        if home_score is None or away_score is None:
            continue  # match not finished yet

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
    raw_fixtures = _fetch_openfootball()
    matches = _normalize_openfootball(raw_fixtures)

    logger.info("Fetching results from TheSportsDB...")
    sportsdb_results = _normalize_thesportsdb(_fetch_thesportsdb())

    # Overlay TheSportsDB scores onto openfootball fixtures
    for match in matches:
        key = match["source_id"]
        if key in sportsdb_results:
            match.update(sportsdb_results[key])
            logger.debug(f"Score updated from TheSportsDB: {key}")

    logger.info(f"Total matches loaded: {len(matches)}")
    return matches

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
                existing.played     = True
                updated_count += 1
        else:
            db.add(Match(
                source_id  = m["source_id"],
                home_team  = m["home_team"],
                away_team  = m["away_team"],
                match_date = m["kickoff_time"],
                stage      = m["stage"],
                home_score = m["home_score"],
                away_score = m["away_score"],
                played     = m["finished"],
            ))
            new_count += 1

    db.commit()
    logger.info(f"Sync complete: {new_count} new, {updated_count} updated.")



# ── Quick test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    matches = get_worldcup_matches()
    for m in matches:
        score = (
            f"{m['home_score']} - {m['away_score']}"
            if m["finished"]
            else "not played yet"
        )
        print(f"{m['kickoff_time']:%Y-%m-%d}  {m['home_team']:20} vs {m['away_team']:20}  {score}")
