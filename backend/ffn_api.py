"""Client helpers for the Fantasy Football Nerd API."""
from __future__ import annotations
import os
import requests
from typing import Any, Dict

BASE_URL = "https://api.fantasyfootballnerd.com/v1"
DEFAULT_API_KEY = "TEST"


def _get(endpoint: str, api_key: str | None = None, **params: Any) -> Dict[str, Any]:
    key = api_key or os.getenv("FFN_API_KEY", DEFAULT_API_KEY)
    if not key:
        raise ValueError("Fantasy Football Nerd API key is required")
    url = f"{BASE_URL}/{endpoint}/json/{key}"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_players(api_key: str | None = None) -> Dict[str, Any]:
    """Return all players from the API."""
    return _get("players", api_key)


def get_injuries(api_key: str | None = None) -> Dict[str, Any]:
    """Return current injury reports."""
    return _get("injuries", api_key)


def get_projections(week: int, position: str, api_key: str | None = None) -> Dict[str, Any]:
    """Return weekly projections for a position."""
    return _get("projections", api_key, week=week, position=position)


def get_schedule(week: int, api_key: str | None = None) -> Dict[str, Any]:
    """Return the NFL schedule for a given week.

    Parameters
    ----------
    week : int
        Regular-season week number.
    api_key : str, optional
        Fantasy Football Nerd API key.  If ``None`` the key is pulled from
        ``FFN_API_KEY``.

    Returns
    -------
    dict
        Response payload with a top-level ``Schedule`` list.  Each element of
        the list contains information about a game such as ``gameId``,
        ``gameDate``, ``awayTeam``, ``homeTeam``, and kickoff time fields.
    """

    return _get("schedule", api_key, week=week)


def get_depth_charts(team: str, api_key: str | None = None) -> Dict[str, Any]:
    """Return the depth chart for a team.

    Parameters
    ----------
    team : str
        NFL team abbreviation (e.g., ``"GB"`` for Green Bay).
    api_key : str, optional
        Fantasy Football Nerd API key.  If ``None`` the key is pulled from
        ``FFN_API_KEY``.

    Returns
    -------
    dict
        Response object with a ``DepthCharts`` mapping.  Each position key such
        as ``QB`` or ``RB`` contains a list of players ordered by depth chart
        rank.
    """

    return _get("depth-charts", api_key, team=team)


def get_rankings(
    week: int, position: str, api_key: str | None = None, ppr: bool = False
) -> Dict[str, Any]:
    """Return weekly fantasy player rankings.

    Parameters
    ----------
    week : int
        Regular-season week number.
    position : str
        Player position abbreviation (``QB``, ``RB``, ``WR``, ``TE``, ``K``,
        or ``DEF``).
    api_key : str, optional
        Fantasy Football Nerd API key.  If ``None`` the key is pulled from
        ``FFN_API_KEY``.
    ppr : bool, optional
        When ``True`` the rankings are returned using PPR scoring.  Defaults to
        ``False``.

    Returns
    -------
    dict
        Response payload with a ``Rankings`` list of player dictionaries
        containing fields such as ``playerId``, ``name``, ``team``, ``position``,
        and ``rank``.
    """

    return _get(
        "rankings", api_key, week=week, position=position, ppr=int(ppr)
    )


def get_bye_weeks(season: int, api_key: str | None = None) -> Dict[str, Any]:
    """Return bye weeks for all teams in a season.

    Parameters
    ----------
    season : int
        Year of the NFL season.
    api_key : str, optional
        Fantasy Football Nerd API key.  If ``None`` the key is pulled from
        ``FFN_API_KEY``.

    Returns
    -------
    dict
        Response object with a ``ByeWeeks`` list.  Each item contains the team
        abbreviation and its corresponding bye week number.
    """

    return _get("bye-weeks", api_key, season=season)
