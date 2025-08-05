from fastapi import FastAPI, HTTPException, Query
from .data_service import load_player_pool
from .store import DraftState
from . import ffn_api

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


@app.get("/ffn/players")
def ffn_players() -> dict:
    """Return raw player data from Fantasy Football Nerd."""
    return ffn_api.get_players()


@app.get("/injuries")
def injuries() -> dict:
    """Return current injury reports."""
    return ffn_api.get_injuries()


@app.get("/projections")
def projections(
    week: int = Query(..., ge=1, le=18),
    position: str = Query(...),
) -> dict:
    """Return weekly projections for a position."""
    pos = position.upper()
    valid_positions = {"QB", "RB", "WR", "TE", "K", "DEF"}
    if pos not in valid_positions:
        raise HTTPException(status_code=400, detail="Invalid position")
    return ffn_api.get_projections(week=week, position=pos)


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
