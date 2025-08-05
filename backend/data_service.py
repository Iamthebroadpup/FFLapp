"""Utilities for loading and merging player data."""
from __future__ import annotations

from typing import Any, Dict, List
from functools import lru_cache

from scoring import from_ffn_projection
from .ffn_api import get_players, get_injuries, get_projections
from .nfl_data import get_play_by_play


def _normalize_projection(proj: Dict[str, Any]) -> Dict[str, Any]:
    """Return a projection dict with numeric fields converted."""
    cleaned: Dict[str, Any] = {}
    for key, value in proj.items():
        if isinstance(value, str):
            try:
                num = float(value)
            except ValueError:
                cleaned[key] = value
            else:
                # Cast integers without decimals to ``int`` for cleanliness
                cleaned[key] = int(num) if num.is_integer() else num
        else:
            cleaned[key] = value
    return cleaned


@lru_cache(maxsize=None)
def _get_projections_cached(week: int, position: str) -> Dict[str, Any]:
    """Cached wrapper around :func:`get_projections`."""
    return get_projections(week, position)


def load_player_pool(year: int = 2023, week: int = 1) -> List[Dict]:
    """Return a list of player dictionaries ready for drafting.

    The function combines:
    - Fantasy Football Nerd player list and current injuries.
    - Weekly projections for each position.
    - Historical play-by-play data from the nflverse releases for
      simple metrics such as games played or missed.
    """
    ffn_players = get_players()
    injuries = get_injuries()

    projections: Dict[str, Dict] = {}
    # Attempt to gather weekly projections for common positions.
    for pos in {"QB", "RB", "WR", "TE"}:
        try:
            resp = get_projections(week=1, position=pos)
            for prj in resp.get("Projections", []):
                pid = prj.get("playerId")
                if pid:
                    projections[pid] = from_ffn_projection(prj)
        except Exception:  # pragma: no cover - network may fail in tests
            continue

    injury_map = {i.get("playerId"): i for i in injuries.get("Injuries", [])}

    # Retrieve projections for each position once and store in a map keyed by
    # playerId.  Network failures are tolerated and simply result in missing
    # projection data.
    positions = {p.get("position") for p in ffn_players.get("Players", [])}
    projection_map: Dict[str, Dict[str, Any]] = {}
    for pos in positions:
        try:
            proj_resp = _get_projections_cached(week, pos)
            for proj in proj_resp.get("Projections", []):
                pid = proj.get("playerId")
                if pid:
                    projection_map[pid] = _normalize_projection(proj)
        except Exception:  # pragma: no cover - network may fail in tests
            continue

    players = []
    for p in ffn_players.get("Players", []):
        pid = p.get("playerId")

        players.append(
            {
                "id": pid,
                "name": p.get("displayName"),
                "position": p.get("position"),
                "team": p.get("team"),
                "injury": injury_map.get(pid),
                "projection": projections.get(pid),
                # Placeholder: real implementation would merge stats from nflverse
                "rookie": False,
            }
        )


    # Placeholder call to show how nflverse data could be incorporated
    try:
        pbp = get_play_by_play(year)
        _ = len(pbp)  # suppress unused variable warning
    except Exception:  # pragma: no cover - network may fail in tests
        pass

    return players
