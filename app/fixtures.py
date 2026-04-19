"""
fixtures.py
-----------
Fetches upcoming World Cup 2026 fixtures from the football-data.org free API.
Returns the next scheduled match and a full list of upcoming fixtures.

Free tier: 10 requests/minute, no credit card needed.
Sign up at https://www.football-data.org/client/register to get your free API key.

Usage:
    Set your key in a .env file:  FOOTBALL_API_KEY=your_key_here
    Or pass it directly:          get_next_match(api_key="your_key")
"""

import os
import requests
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL    = "https://api.football-data.org/v4"
WC_2026_ID  = 2000   # football-data.org competition ID for FIFA World Cup
HEADERS     = lambda key: {"X-Auth-Token": key}
# ---------------------------------------------------------------------------


@dataclass
class Fixture:
    """A single upcoming match."""
    home_team:  str
    away_team:  str
    kickoff:    datetime      # timezone-aware UTC datetime
    competition: str
    matchday:   Optional[int]
    status:     str           # SCHEDULED | LIVE | IN_PLAY | FINISHED

    @property
    def kickoff_local(self) -> str:
        """Return kickoff as a readable local-time string."""
        return self.kickoff.astimezone().strftime("%d %b %Y  %H:%M")

    @property
    def seconds_until(self) -> float:
        """Seconds from now until kickoff (negative if in the past)."""
        return (self.kickoff - datetime.now(timezone.utc)).total_seconds()

    @property
    def is_upcoming(self) -> bool:
        return self.seconds_until > 0


def get_fixtures(api_key: str, limit: int = 10) -> list[Fixture]:
    """
    Fetch upcoming World Cup 2026 fixtures.

    Args:
        api_key : Your football-data.org API key.
        limit   : Maximum number of fixtures to return.

    Returns:
        List of Fixture objects sorted by kickoff time (soonest first).
    """
    if not api_key:
        logger.warning("No API key provided — returning mock fixtures.")
        return _mock_fixtures()

    try:
        url = f"{BASE_URL}/competitions/{WC_2026_ID}/matches"
        params = {"status": "SCHEDULED", "limit": limit}
        resp = requests.get(url, headers=HEADERS(api_key), params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error("Fixtures API call failed: %s — falling back to mock data.", e)
        return _mock_fixtures()

    fixtures = []
    for match in data.get("matches", []):
        try:
            kickoff = datetime.fromisoformat(
                match["utcDate"].replace("Z", "+00:00")
            )
            fixtures.append(Fixture(
                home_team   = match["homeTeam"]["name"],
                away_team   = match["awayTeam"]["name"],
                kickoff     = kickoff,
                competition = match.get("competition", {}).get("name", "World Cup 2026"),
                matchday    = match.get("matchday"),
                status      = match.get("status", "SCHEDULED"),
            ))
        except (KeyError, ValueError) as e:
            logger.warning("Skipping malformed match entry: %s", e)

    fixtures.sort(key=lambda f: f.kickoff)
    return fixtures[:limit]


def get_next_match(api_key: str) -> Optional[Fixture]:
    """Return the single next upcoming fixture, or None if none found."""
    upcoming = [f for f in get_fixtures(api_key) if f.is_upcoming]
    return upcoming[0] if upcoming else None


# ---------------------------------------------------------------------------
# Mock data — used when no API key is set (for local dev / testing)
# These are realistic World Cup 2026 group stage fixtures
# ---------------------------------------------------------------------------

def _mock_fixtures() -> list[Fixture]:
    now = datetime.now(timezone.utc)
    matches = [
        ("USA",       "Mexico",      11),
        ("Brazil",    "Argentina",   11),
        ("France",    "England",     12),
        ("Germany",   "Spain",       12),
        ("Portugal",  "Morocco",     13),
        ("Japan",     "South Korea", 13),
    ]
    fixtures = []
    for i, (home, away, day) in enumerate(matches):
        from datetime import timedelta
        kickoff = now + timedelta(days=i+1, hours=2)
        fixtures.append(Fixture(
            home_team   = home,
            away_team   = away,
            kickoff     = kickoff,
            competition = "FIFA World Cup 2026 (Mock)",
            matchday    = day,
            status      = "SCHEDULED",
        ))
    return fixtures


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    key = os.getenv("FOOTBALL_API_KEY", "")
    fixtures = get_fixtures(key, limit=5)
    for f in fixtures:
        print(f"  {f.home_team} vs {f.away_team}  |  {f.kickoff_local}  |  in {f.seconds_until/3600:.1f}h")
