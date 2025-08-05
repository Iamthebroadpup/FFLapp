import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from scoring import calculate_points, from_ffn_projection
from scoring.rules import ScoringRules

from backend import data_service


def test_from_ffn_projection_maps_keys():
    raw = {
        "passingYds": 250,
        "passingTD": 2,
        "passingInt": 1,
        "rushingYds": 20,
        "rushingTD": 1,
        "receivingYds": 0,
        "receivingTD": 0,
        "receptions": 0,
    }
    stats = from_ffn_projection(raw)
    assert stats == {
        "passing_yards": 250,
        "passing_tds": 2,
        "interceptions": 1,
        "rushing_yards": 20,
        "rushing_tds": 1,
        "receiving_yards": 0,
        "receiving_tds": 0,
        "receptions": 0,
    }

    # Ensure the translated stats work with calculate_points
    rules = ScoringRules()
    points = calculate_points(stats, rules)
    assert isinstance(points, float)


def test_load_player_pool_includes_projection(monkeypatch):
    players_resp = {
        "Players": [
            {
                "playerId": "1",
                "displayName": "John Doe",
                "position": "QB",
                "team": "FA",
            }
        ]
    }

    injuries_resp = {"Injuries": []}

    projections_resp = {
        "Projections": [
            {"playerId": "1", "passingYds": 300, "passingTD": 3}
        ]
    }

    monkeypatch.setattr(
        data_service, "get_players", lambda: players_resp
    )
    monkeypatch.setattr(
        data_service, "get_injuries", lambda: injuries_resp
    )
    monkeypatch.setattr(
        data_service, "get_projections", lambda week, position: projections_resp
    )

    players = data_service.load_player_pool()
    assert players[0]["projection"] == {
        "passing_yards": 300,
        "passing_tds": 3,
    }

