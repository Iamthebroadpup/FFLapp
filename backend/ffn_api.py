"""Client helpers for the Fantasy Football Nerd API."""
from __future__ import annotations
import os
import requests
from typing import Any, Dict

BASE_URL = "https://api.fantasyfootballnerd.com/v1"


def _get(endpoint: str, api_key: str | None = None, **params: Any) -> Dict[str, Any]:
    key = api_key or os.getenv("FFN_API_KEY")
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
