from fastapi import FastAPI, HTTPException
from .data_service import load_player_pool
from .store import DraftState

app = FastAPI(title="Draft Day Assistant")
state = DraftState.load()

@app.on_event("startup")
def startup() -> None:
    """Load player data at startup."""
    players = load_player_pool()
    state.set_players(players)


@app.get("/players")
def get_players() -> list:
    """Return all available players."""
    return state.available_players


@app.post("/draft/pick")
def pick_player(player_id: str, team: int) -> dict:
    """Record a draft pick and remove the player from the pool."""
    try:
        state.make_pick(player_id, team)
    except ValueError as exc:  # pragma: no cover - simple example
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True}


@app.post("/draft/undo")
def undo_pick() -> dict:
    """Undo the last pick."""
    state.undo_pick()
    return {"ok": True}


@app.get("/state")
def get_state() -> dict:
    """Return the full draft state."""
    return state.to_dict()
