from __future__ import annotations
import os
from typing import Dict, List, Tuple
import httpx
from dotenv import load_dotenv, find_dotenv

# Robustly load the nearest .env (works even if CWD isn't /backend)
load_dotenv(find_dotenv())


class SportsDataError(Exception):
    pass


def _season_str(year: int, season_type: str) -> str:
    return f"{year}{season_type.upper()}"  # e.g., 2025REG


def _api_base() -> str:
    # Allow override via .env if you want to point to a mock/base
    return os.getenv("SPORTSDATAIO_BASE", "https://api.sportsdata.io/v3/nfl")


def _headers() -> dict:
    key = os.getenv("SPORTSDATAIO_API_KEY")
    if not key:
        raise SportsDataError("Missing SportsDataIO API key")
    return {"Ocp-Apim-Subscription-Key": key}


async def _get_json(client: httpx.AsyncClient, path: str):
    url = f"{_api_base()}{path}"
    r = await client.get(url, headers=_headers(), timeout=30)
    if r.status_code == 404:
        raise SportsDataError(f"404 {path}")
    r.raise_for_status()
    return r.json()


async def fetch_projections_and_adp_and_dst(
    year: int, season_type: str
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Returns: (player_projections, fantasy_players_adp, dst_projections)
    - Player projections include QB/RB/WR/TE/K (same feed).
    - DST projections come from a fantasy defense projections feed (separate).
    """
    seasonA = _season_str(year, season_type)

    proj_path = f"/projections/json/PlayerSeasonProjectionStats/{seasonA}"
    adp_path = "/stats/json/FantasyPlayers"

    # Try a few common DST season endpoints. We use the first that works.
    dst_candidates = [
        f"/projections/json/FantasyDefenseSeasonProjections/{seasonA}",
        f"/projections/json/FantasyDefenseProjectionsBySeason/{seasonA}",
        f"/projections/json/FantasyDefenseProjections/{seasonA}",
    ]

    async with httpx.AsyncClient() as client:
        proj_data = await _get_json(client, proj_path)

        try:
            adp_data = await _get_json(client, adp_path)
        except Exception:
            adp_data = []

        dst_data: List[Dict] = []
        for p in dst_candidates:
            try:
                dst_data = await _get_json(client, p)
                if isinstance(dst_data, list) and len(dst_data) > 0:
                    break
            except Exception:
                continue  # try next

    return proj_data, adp_data, dst_data


def normalize_player(row: Dict) -> Dict:
    pid = int(row.get("PlayerID") or row.get("PlayerId") or row.get("Id") or 0)
    name = row.get("Name") or f"Player {pid}"
    team = row.get("Team")
    pos = row.get("Position") or row.get("FantasyPosition") or "UNK"
    bye = row.get("ByeWeek")
    adp = row.get("AverageDraftPosition")
    adp_ppr = row.get("AverageDraftPositionPPR") or row.get("AverageDraftPositionPpr")

    proj = {
        "passing_yards": row.get("PassingYards", 0) or row.get("PassYards", 0),
        "passing_tds": row.get("PassingTouchdowns", 0) or row.get("PassTouchdowns", 0),
        "interceptions": row.get("PassingInterceptions", 0) or row.get("Interceptions", 0),
        "rushing_yards": row.get("RushingYards", 0),
        "rushing_tds": row.get("RushingTouchdowns", 0),
        "receptions": row.get("Receptions", 0),
        "receiving_yards": row.get("ReceivingYards", 0),
        "receiving_tds": row.get("ReceivingTouchdowns", 0),
        "fumbles_lost": row.get("FumblesLost", 0) or row.get("Fumbles", 0),
        "two_pt": (row.get("TwoPointConversionPasses", 0) or 0)
        + (row.get("TwoPointConversionRuns", 0) or 0)
        + (row.get("TwoPointConversionReceptions", 0) or 0),
        # Kickers come through same feed:
        "fg_made": row.get("FieldGoalsMade", 0) or row.get("FieldGoals", 0) or 0,
        "xp_made": row.get("ExtraPointsMade", 0) or 0,
    }
    return {
        "player_id": pid,
        "name": name,
        "team": team,
        "position": pos,
        "bye_week": bye,
        "adp": adp,
        "adp_ppr": adp_ppr,
        "projections": proj,
    }


def normalize_dst(row: Dict) -> Dict:
    # Some DST feeds have FantasyDefenseID, others include PlayerID for joins.
    pid = int(row.get("PlayerID") or row.get("PlayerId") or row.get("FantasyDefenseID") or 0)
    team = row.get("Team")
    name = f"{team} DST" if team else (row.get("Name") or "DST")
    dst = {
        "sacks": row.get("Sacks", 0) or 0,
        "interceptions": row.get("Interceptions", 0) or 0,
        "fumbles_recovered": row.get("FumblesRecovered", 0) or 0,
        "safeties": row.get("Safeties", 0) or 0,
        "def_tds": (row.get("DefensiveTouchdowns", 0) or row.get("TouchdownsScored", 0) or 0),
        "return_tds": (row.get("SpecialTeamsTouchdowns", 0) or 0),
        "points_allowed": row.get("PointsAllowed", 21) or 21,
    }
    return {
        "player_id": pid,
        "name": name,
        "team": team,
        "position": "DST",
        "bye_week": row.get("ByeWeek"),
        "adp": row.get("AverageDraftPosition"),
        "adp_ppr": row.get("AverageDraftPositionPPR") or row.get("AverageDraftPositionPpr"),
        "projections": {},  # not used for DST calc
        "dst": dst,
    }


def merge_adp(base: Dict[int, Dict], adp_rows: List[Dict]) -> None:
    for r in adp_rows:
        pid = int(r.get("PlayerID") or r.get("PlayerId") or r.get("Id") or 0)
        if pid == 0:
            continue
        b = base.get(pid)
        if not b:
            continue
        adp = r.get("AverageDraftPosition")
        adp_ppr = r.get("AverageDraftPositionPPR") or r.get("AverageDraftPositionPpr")
        pos = r.get("Position") or r.get("FantasyPosition")
        if adp is not None:
            b["adp"] = adp
        if adp_ppr is not None:
            b["adp_ppr"] = adp_ppr
        if pos and not b.get("position"):
            b["position"] = pos
