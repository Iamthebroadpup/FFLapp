"""Simple JSON file persistence for draft state."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

STATE_FILE = Path("draft_state.json")


@dataclass
class DraftState:
    teams: int = 12
    picks: List[Dict[str, Any]] = field(default_factory=list)
    available_players: List[Dict[str, Any]] = field(default_factory=list)
    filename: Path = STATE_FILE

    def set_players(self, players: List[Dict[str, Any]]) -> None:
        self.available_players = players
        self._save()

    def make_pick(self, player_id: str, team: int) -> None:
        player = next((p for p in self.available_players if p["id"] == player_id), None)
        if not player:
            raise ValueError("Player not available")
        self.available_players = [p for p in self.available_players if p["id"] != player_id]
        self.picks.append({"team": team, "player": player})
        self._save()

    def undo_pick(self) -> None:
        if not self.picks:
            return
        last = self.picks.pop()
        self.available_players.append(last["player"])
        self._save()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "teams": self.teams,
            "picks": self.picks,
            "available_players": self.available_players,
        }

    def _save(self) -> None:
        self.filename.write_text(json.dumps(self.to_dict()))

    @classmethod
    def load(cls, filename: Path = STATE_FILE) -> "DraftState":
        if filename.exists():
            data = json.loads(filename.read_text())
            return cls(
                teams=data.get("teams", 12),
                picks=data.get("picks", []),
                available_players=data.get("available_players", []),
                filename=filename,
            )
        return cls(filename=filename)
