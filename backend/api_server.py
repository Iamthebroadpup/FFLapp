from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal, List
from clients.fantasy_nerds import get_players, get_draft_rankings, get_adp, NerdsError
from suggestion import compute_vor

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class LeagueSettings(BaseModel):
    teams: int = 14
    scoring: Literal["std","ppr","half","superflex"] = "half"
    roster: dict[str, int] = {"QB":1,"RB":2,"WR":2,"TE":1,"FLEX":1,"K":1,"DST":1,"BENCH":7}

@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/bootstrap")
def bootstrap(settings: LeagueSettings):
    try:
        players = get_players(include_inactive=0)            # source of truth universe
        ranks = get_draft_rankings(settings.scoring)         # projected season points
        adp = get_adp(settings.teams, settings.scoring)      # ADP calibrated to league size
        return {"players": players, "ranks": ranks, "adp": adp}
    except NerdsError as e:
        raise HTTPException(502, f"FantasyNerds error: {e}")

class SuggestRequest(LeagueSettings):
    picked_ids: List[str] = []

@app.post("/api/suggestions")
def suggestions(body: SuggestRequest):
    try:
        ranks = get_draft_rankings(body.scoring)["players"]
        picked = set(body.picked_ids)
        ranks = [p for p in ranks if p.get("player_id") not in picked]
        return compute_vor(ranks, body.roster, body.teams)[:24]
    except NerdsError as e:
        raise HTTPException(502, f"FantasyNerds error: {e}")
