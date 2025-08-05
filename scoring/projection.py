"""Utilities for working with Fantasy Football Nerd projections."""

from __future__ import annotations

from typing import Dict


# Mapping of Fantasy Football Nerd projection keys to the internal
# statistics names expected by ``calculate_points``.
FFN_KEY_MAP: Dict[str, str] = {
    "passingYds": "passing_yards",
    "passingTD": "passing_tds",
    "passingInt": "interceptions",
    "rushingYds": "rushing_yards",
    "rushingTD": "rushing_tds",
    "receivingYds": "receiving_yards",
    "receivingTD": "receiving_tds",
    # Some feeds may use ``receptions`` while others use ``rec``.
    "receptions": "receptions",
    "rec": "receptions",
}


def from_ffn_projection(projection: Dict[str, float]) -> Dict[str, float]:
    """Translate a raw FFN projection into stats for ``calculate_points``.

    Parameters
    ----------
    projection:
        A dictionary returned by the Fantasy Football Nerd ``projections``
        endpoint.  The keys in this dictionary use FFN's naming conventions
        (e.g. ``passingYds`` or ``rushingTD``).

    Returns
    -------
    Dict[str, float]
        A new dictionary containing only the statistics understood by
        :func:`scoring.calculate_points`.
    """

    stats: Dict[str, float] = {}
    for ffn_key, std_key in FFN_KEY_MAP.items():
        if ffn_key in projection:
            stats[std_key] = projection[ffn_key]
    return stats


__all__ = ["from_ffn_projection"]

