import os, httpx
from typing import Literal

BASE = "https://api.fantasynerds.com/v1/nfl"
APIKEY = os.getenv("FANTASY_NERDS_API_KEY", "TEST")  # TEST returns sample data

class NerdsError(RuntimeError): pass

def _get(path: str, params: dict | None = None):
    params = dict(params or {})
    params["apikey"] = APIKEY
    try:
        with httpx.Client(timeout=20) as c:
            r = c.get(f"{BASE}/{path}", params=params)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise NerdsError(f"{e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        raise NerdsError(str(e))

def get_players(include_inactive: int = 0):
    return _get("players", {"include_inactive": include_inactive})

def get_draft_rankings(fmt: Literal["std","ppr","half","superflex"] = "std"):
    return _get("draft-rankings", {"format": fmt})

def get_adp(teams: int = 12, fmt: Literal["std","ppr","half","superflex"] = "std"):
    return _get("adp", {"teams": teams, "format": fmt})
