import os
import httpx
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

API_KEY = (
    os.getenv("SPORTSDATA_API_KEY")
    or os.getenv("SPORTSDATA_IO_KEY")
    or os.getenv("SPORTSDATA_KEY")
)
if not API_KEY:
    # We won't raise here—FastAPI /api/init will return a clear error if key is missing.
    pass

BASE = "https://api.sportsdata.io/v3/nfl"
BASE_SCORES = f"{BASE}/scores/json"
BASE_STATS  = f"{BASE}/stats/json"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY} if API_KEY else {}

def _season_clean(s: str | int) -> str:
    s = str(s)
    return s.replace("REG", "").replace("POST", "").replace("PRE", "")

async def _get(client: httpx.AsyncClient, url: str) -> Any:
    r = await client.get(url, headers=HEADERS, timeout=30.0)
    r.raise_for_status()
    return r.json()

async def _get_path(client: httpx.AsyncClient, path: str) -> Any:
    url = f"{BASE}{path}"
    r = await client.get(url, headers=HEADERS, timeout=30.0)
    r.raise_for_status()
    return r.json()

async def fetch_player_projections(season: str | int) -> List[Dict[str, Any]]:
    """
    Try several valid projections routes + several season formats.
    Some accounts/seasons only exist as PRE or REG during August.
    """
    year = _season_clean(season)
    season_forms = [year, f"{year}REG", f"{year}PRE"]
    path_templates = [
        "/projections/json/PlayerSeasonProjectionStats/{s}",          # includes ADP
        "/projections/json/PlayerSeasonProjectionStatsWithADP/{s}",   # legacy alias, includes ADP
        "/projections/json/PlayerSeasonProjectedStats/{s}",           # fallback (no ADP)
    ]

    errs: List[str] = []
    async with httpx.AsyncClient() as client:
        for s in season_forms:
            for tpl in path_templates:
                path = tpl.format(s=s)
                try:
                    data = await _get_path(client, path)
                    return data if isinstance(data, list) else []
                except httpx.HTTPStatusError as e:
                    errs.append(f"{e.response.status_code} {path}")
                    continue
    # If nothing worked, return empty list (caller will fall back to season stats)
    return []

async def fetch_player_season_stats(season: int | str) -> List[Dict[str, Any]]:
    """
    Broadly-available season stats endpoint as a fallback when projections are unavailable.
    """
    year = int(_season_clean(season))
    async with httpx.AsyncClient() as client:
        url = f"{BASE_STATS}/PlayerSeasonStats/{year}"
        try:
            data = await _get(client, url)
            return data if isinstance(data, list) else []
        except Exception:
            return []

async def fetch_injuries(season: int | str) -> List[Dict[str, Any]]:
    year = _season_clean(season)
    async with httpx.AsyncClient() as client:
        for url in (f"{BASE_SCORES}/Injuries/{year}", f"{BASE_STATS}/Injuries/{year}"):
            try:
                data = await _get(client, url)
                if isinstance(data, list):
                    return data
            except Exception:
                continue
    return []

async def fetch_all_data(season: str) -> Dict[str, Any]:
    """
    Pull: players, byes, depth charts, projections (if available),
    injuries (best effort), and fallback season stats (prev year) if projections are empty.
    """
    if not API_KEY:
        raise RuntimeError("Missing SportsData.io API key (set SPORTSDATA_API_KEY).")

    s = _season_clean(season)
    year = int(s)

    async with httpx.AsyncClient() as client:
        players = await _get(client, f"{BASE_SCORES}/PlayersByAvailable")
        byes    = await _get(client, f"{BASE_SCORES}/Byes/{s}")
        depth   = await _get(client, f"{BASE_SCORES}/DepthChartsAll")

    projections = await fetch_player_projections(year)
    injuries    = await fetch_injuries(year)

    # If projections are missing (404s), fall back to last season stats
    season_stats = []
    if not projections:
        season_stats = await fetch_player_season_stats(year - 1)

    return {
        "players": players or [],
        "byes": byes or [],
        "depth": depth or [],
        "projections": projections or [],
        "season_stats": season_stats or [],  # NEW: used as a fallback in util.normalize_players
        "injuries": injuries or [],
    }
