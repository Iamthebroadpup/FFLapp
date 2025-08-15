from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import Player, SuggestionV2, ScoringRules, LeagueContext, StrategyProfile
import providers.sportsdata as sportsdata  # robust module import
from logic.util import normalize_players
from logic.engine_v2.reproject import reproject_points
from logic.engine_v2.utility import suggest_v2

# ---- FastAPI app + CORS ----
app = FastAPI(title="Fantasy Draft Assistant API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev: loosen for local, tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- In-memory data store ----
DATA: Dict[str, Any] = {
    "players": {},      # pid -> Player
    "undrafted": set(), # set[pid]
    "drafted": [],      # list[{"playerId": int, "teamName": str}]
    "history": [],      # events (optional for engine)
    "rules": ScoringRules().dict(),
    "context": LeagueContext().dict(),
    "strategy": StrategyProfile().dict(),
    "opponents": {},
}

# ---- Request models ----
class DraftReq(BaseModel):
    playerId: int
    teamName: str

class UndraftReq(BaseModel):
    playerId: int


# ---- Helpers ----
def _my_bye_counts() -> Dict[int, int]:
    """Count byes on MY roster; used by engine for balancing bye weeks."""
    counts: Dict[int, int] = {}
    pid_map: Dict[int, Player] = DATA["players"]
    for d in DATA["drafted"]:
        if d.get("teamName") != "ME":
            continue
        pid = d["playerId"]
        p = pid_map.get(pid)
        if not p:
            continue
        if p.bye_week is None:
            continue
        counts[p.bye_week] = counts.get(p.bye_week, 0) + 1
    return counts


async def _fetch_all_wrapper(season: Optional[int] = None) -> Dict[str, Any]:
    """
    Call whichever entrypoint exists in providers.sportsdata.
    Expected to return a dict with keys: players, projections, byes, depth, season_stats
    """
    # Try the common names in order:
    if hasattr(sportsdata, "fetch_all"):
        return await sportsdata.fetch_all(season)
    if hasattr(sportsdata, "fetch_all_data"):
        return await sportsdata.fetch_all_data(season)
    if hasattr(sportsdata, "fetch_all_sources"):
        return await sportsdata.fetch_all_sources(season)
    if hasattr(sportsdata, "get_all"):
        return await sportsdata.get_all(season)
    raise RuntimeError(
        "providers.sportsdata is missing a fetch_all-like function. "
        "Please expose fetch_all(season) or alias your existing entrypoint."
    )


# ---- Endpoints ----
@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/init")
async def init(season: Optional[int] = None):
    """
    Fetch all data from SportsData and build our in-memory dataset.
    """
    try:
        raw = await _fetch_all_wrapper(season)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SportsData fetch failed: {e}")

    players = normalize_players(raw)

    DATA["players"] = players
    DATA["undrafted"] = set(players.keys())
    DATA["drafted"] = []
    # Keep rules/context/strategy unless you want to reset them too

    return {
        "players_count": len(players),
        "depth_teams": len({p.team for p in players.values() if p.team}),
        "bye_count": len({p.bye_week for p in players.values() if p.bye_week}),
    }


@app.get("/api/players", response_model=List[Player])
def list_players(q: Optional[str] = None, pos: Optional[str] = None):
    """
    Return UNDRAFTED players (with optional filters).
    If undrafted set is empty (bad state), fall back to all players so UI never blanks.
    """
    # Primary source = undrafted
    if DATA["undrafted"]:
        players = [p for pid, p in DATA["players"].items() if pid in DATA["undrafted"]]
    else:
        # Fallback so the UI doesn't go blank if undrafted got wiped
        players = list(DATA["players"].values())

    # Filters
    if pos:
        players = [p for p in players if (p.position or "").upper() == pos.upper()]
    if q:
        ql = q.lower()
        players = [p for p in players if ql in p.name.lower() or (p.team and ql in p.team.lower())]

    # Only fill missing projected_points (do NOT overwrite feed values)
    rules = ScoringRules(**DATA["rules"])
    try:
        pts = reproject_points(players, rules)
        for i, p in enumerate(players):
            if p.projected_points is None:
                try:
                    p.projected_points = float(pts[i])
                except Exception:
                    pass
    except Exception:
        pass

    # Sort: projection desc, ADP asc, Name
    players.sort(key=lambda p: (-(p.projected_points or 0.0), p.adp or 9999, p.name))
    return players


@app.get("/api/undrafted", response_model=List[Player])
def get_undrafted(pos: Optional[str] = None, q: Optional[str] = None):
    """
    Direct UNDRAFTED list with optional filters — useful as a frontend fallback.
    """
    if DATA["undrafted"]:
        players = [DATA["players"][pid] for pid in DATA["undrafted"]]
    else:
        players = list(DATA["players"].values())

    # Filters
    if pos:
        players = [p for p in players if (p.position or "").upper() == pos.upper()]
    if q:
        ql = q.lower()
        players = [p for p in players if ql in p.name.lower() or (p.team and ql in p.team.lower())]

    # Only fill missing projected_points (do NOT overwrite feed values)
    rules = ScoringRules(**DATA["rules"])
    try:
        pts = reproject_points(players, rules)
        for i, p in enumerate(players):
            if p.projected_points is None:
                try:
                    p.projected_points = float(pts[i])
                except Exception:
                    pass
    except Exception:
        pass

    return players


@app.get("/api/drafted")
def get_drafted():
    # Return [{ player, teamName }]
    out = []
    for d in DATA["drafted"]:
        pid = d["playerId"]
        p = DATA["players"].get(pid)
        if not p:
            continue
        out.append({"player": p, "teamName": d["teamName"]})
    return out


@app.post("/api/draft")
def draft(req: DraftReq):
    pid = req.playerId
    if pid not in DATA["players"]:
        raise HTTPException(status_code=404, detail="Unknown player")
    if pid not in DATA["undrafted"]:
        # already drafted
        return {"ok": True}
    DATA["undrafted"].remove(pid)
    DATA["drafted"].append({"playerId": pid, "teamName": req.teamName})
    DATA["history"].append({"t": "draft", "pid": pid, "teamName": req.teamName})
    return {"ok": True}


@app.post("/api/undraft")
def undraft(req: UndraftReq):
    pid = req.playerId
    # Remove latest matching drafted entry (in case drafted more than once in history)
    for i in range(len(DATA["drafted"]) - 1, -1, -1):
        if DATA["drafted"][i]["playerId"] == pid:
            DATA["drafted"].pop(i)
            break
    DATA["undrafted"].add(pid)
    DATA["history"].append({"t": "undraft", "pid": pid})
    return {"ok": True}


@app.post("/api/rules")
def set_rules(rules: ScoringRules):
    DATA["rules"] = rules.dict()
    return {"ok": True}


@app.post("/api/context")
def set_context(ctx: LeagueContext):
    DATA["context"] = ctx.dict()
    return {"ok": True}


@app.post("/api/strategy")
def set_strategy(strategy: StrategyProfile):
    DATA["strategy"] = strategy.dict()
    return {"ok": True}


@app.get("/api/suggest_v2", response_model=List[SuggestionV2])
def suggest_v2_endpoint(count: int = 12, pos: Optional[str] = None):
    # Prepare inputs for the engine
    all_players = (
        [DATA["players"][pid] for pid in DATA["undrafted"]]
        if DATA["undrafted"]
        else list(DATA["players"].values())
    )
    rules = ScoringRules(**DATA["rules"])
    ctx = LeagueContext(**DATA["context"])
    strategy = StrategyProfile(**DATA["strategy"])
    bye_counts = _my_bye_counts()

    try:
        scored = suggest_v2(
            players=all_players,
            drafted=DATA["drafted"],
            rules=rules,
            ctx=ctx,
            my_bye_counts=bye_counts,
            strategy=strategy,
            count=count,
            pos=pos,
            history=DATA["history"],
            opponents_needs=DATA["opponents"],
        )
        return scored
    except Exception as e:
        # Graceful fallback so UI always shows something
        print("suggest_v2 error:", e)
        pool = all_players
        if pos:
            pool = [p for p in pool if (p.position or "").upper() == pos.upper()]
        pool = sorted(pool, key=lambda p: (-(p.projected_points or 0.0), p.adp or 9999, p.name))
        fallback = [
            SuggestionV2(player=p, score=float(p.projected_points or 0.0))
            for p in pool[:max(1, count)]
        ]
        return fallback


# Back-compat route for older frontends
@app.get("/api/suggest", response_model=List[SuggestionV2])
def suggest_compat(count: int = 12, pos: Optional[str] = None):
    return suggest_v2_endpoint(count=count, pos=pos)


# Debug helper to confirm feed mapping
@app.get("/api/feed_status")
def feed_status():
    players = DATA["players"]
    und = DATA["undrafted"]
    with_proj = (
        sum(1 for pid in und if players[pid].projected_points is not None)
        if und else sum(1 for p in players.values() if p.projected_points is not None)
    )
    with_adp = (
        sum(1 for pid in und if (players[pid].adp or 0) > 0)
        if und else sum(1 for p in players.values() if (p.adp or 0) > 0)
    )
    return {
        "players_count": len(players),
        "undrafted_count": len(und),
        "with_projected_points": with_proj,
        "with_adp": with_adp,
    }
