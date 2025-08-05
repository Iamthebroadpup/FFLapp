"""Utilities for loading and merging player data."""
from __future__ import annotations

from typing import Dict, List

from scoring import from_ffn_projection

from .ffn_api import get_players, get_injuries, get_projections
from .nfl_data import get_play_by_play


def load_player_pool(year: int = 2023) -> List[Dict]:
    """Return a list of player dictionaries ready for drafting.

    The function combines:
    - Fantasy Football Nerd player list and current injuries.
    - Historical play-by-play data from the nflverse releases for
      simple metrics such as games played or missed.

    Full stat/projection merging is left as a future enhancement.
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
