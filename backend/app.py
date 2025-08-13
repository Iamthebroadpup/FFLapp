import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import ScoringRules, Player, Suggestion, InitSummary, LeagueContext, StrategyProfile, SuggestionV2
from providers.sportsdata import fetch_all_data
from logic.util import normalize_players
from logic.engine_v2.utility import suggest_v2

load_dotenv()

app = FastAPI(title="Fantasy Draft Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA: Dict[str, Any] = {
    "players": {},         # player_id -> Player
    "undrafted": set(),    # set of player_ids
    "drafted": {},         # player_id -> teamName
    "rules": ScoringRules().model_dump(),
    "bye_counts": {},      # bye_week -> count (my team only)
    "ctx": LeagueContext().model_dump(),
    "strategy": StrategyProfile().model_dump(),
    "history": [],         # ordered picks: {pid,pos,teamName}
    "opponents": {},       # teamName -> {pos -> starters remaining}
}

def _my_bye_counts() -> Dict[int, int]:
    counts: Dict[int,int] = {}
    for pid, team in DATA["drafted"].items():
        if team != "ME": continue
        p = DATA["players"].get(pid)
        if p and p.bye_week:
            counts[p.bye_week] = counts.get(p.bye_week, 0) + 1
    return counts

def _starter_template(rules: ScoringRules) -> Dict[str,int]:
    return {
        "QB": rules.roster_qb,
        "RB": rules.roster_rb,
        "WR": rules.roster_wr,
        "TE": rules.roster_te,
        "DST": rules.roster_dst,
        "K":  rules.roster_k,
        "FLEX": rules.roster_flex,  # handled as RB/WR/TE consumption
    }

def _recalc_opponents_needs():
    # naive: derive remaining starters (excluding FLEX consumption) for each team by counting drafted positions
    rules = ScoringRules(**DATA["rules"])
    base = _starter_template(rules)
    opps: Dict[str, Dict[str,int]] = {}
    for team in set(DATA["drafted"].values()):
        if team == "ME": continue
        opps[team] = {"QB":base["QB"],"RB":base["RB"],"WR":base["WR"],"TE":base["TE"],"DST":base["DST"],"K":base["K"]}
    for pid, team in DATA["drafted"].items():
        if team == "ME": continue
        p = DATA["players"].get(pid)
        if not p: continue
        pos = (p.position or "").upper()
        if pos in ("QB","RB","WR","TE","DST","K"):
            opps.setdefault(team, {"QB":base["QB"],"RB":base["RB"],"WR":base["WR"],"TE":base["TE"],"DST":base["DST"],"K":base["K"]})
            if opps[team][pos] > 0:
                opps[team][pos] -= 1
            else:
                # treat overflow as flex usage (very rough)
                if pos in ("RB","WR","TE") and base["FLEX"]>0:
                    # we won't track exact flex per team; this is fine for pressure calc
                    pass
    DATA["opponents"] = opps

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/init", response_model=InitSummary)
async def api_init(season: Optional[str] = None):
    season = season or os.getenv("SPORTSDATA_SEASON", "2025")
    try:
        raw = await fetch_all_data(season)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SportsData fetch failed: {e}")

    normalized = normalize_players(raw)

    DATA["players"] = {pid: p for pid, p in normalized.items()}
    DATA["undrafted"] = set(DATA["players"].keys())
    DATA["drafted"] = {}
    DATA["bye_counts"] = {}
    DATA["history"] = {}
    DATA["history"] = []
    DATA["opponents"] = {}

    depth_teams = len({p.team for p in normalized.values() if p.team})
    bye_count = len([p for p in normalized.values() if p.bye_week])
    return InitSummary(players_count=len(DATA["players"]), depth_teams=depth_teams, bye_count=bye_count)

@app.post("/api/keepers")
def apply_keepers(keepers: List[Dict[str, Any]]):
    """
    keepers: [{ "playerId": 123, "teamName": "TeamA" }, ...]
    """
    for k in keepers:
        pid = int(k.get("playerId"))
        team = k.get("teamName") or "OTHER"
        if pid in DATA["players"] and pid in DATA["undrafted"]:
            DATA["undrafted"].remove(pid)
            DATA["drafted"][pid] = team
    DATA["bye_counts"] = _my_bye_counts()
    _recalc_opponents_needs()
    return {"ok": True}

@app.get("/api/players", response_model=List[Player])
def list_players(q: Optional[str] = None, pos: Optional[str] = None):
    players = [p for pid, p in DATA["players"].items() if pid in DATA["undrafted"]]
    if pos:
        players = [p for p in players if (p.position or "").upper() == pos.upper()]
    if q:
        ql = q.lower()
        players = [p for p in players if ql in p.name.lower() or (p.team and ql in p.team.lower())]
    players.sort(key=lambda p: (-(p.projected_points or 0), p.adp or 9999, p.name))
    return players[:500]

@app.post("/api/draft")
def draft_player(payload: dict):
    pid = int(payload.get("playerId"))
    team = payload.get("teamName", "OTHER")
    if pid not in DATA["players"]:
        raise HTTPException(404, "Unknown player")
    if pid not in DATA["undrafted"]:
        raise HTTPException(400, "Player already drafted")
    DATA["undrafted"].remove(pid)
    DATA["drafted"][pid] = team
    DATA["bye_counts"] = _my_bye_counts()
    p = DATA["players"][pid]
    DATA["history"].append({"pid": pid, "pos": (p.position or "").upper(), "teamName": team})
    _recalc_opponents_needs()
    return {"ok": True}

@app.post("/api/undraft")
def undraft_player(payload: dict):
    pid = int(payload.get("playerId"))
    if pid in DATA["drafted"]:
        DATA["undrafted"].add(pid)
        DATA["drafted"].pop(pid, None)
        DATA["bye_counts"] = _my_bye_counts()
        # remove last occurrence from history
        for i in range(len(DATA["history"]) - 1, -1, -1):
            if DATA["history"][i].get("pid") == pid:
                DATA["history"].pop(i); break
        _recalc_opponents_needs()
    return {"ok": True}

@app.get("/api/undrafted", response_model=List[Player])
def get_undrafted():
    return [DATA["players"][pid] for pid in DATA["undrafted"]]

@app.get("/api/drafted")
def get_drafted():
    out = []
    for pid, team in DATA["drafted"].items():
        p = DATA["players"].get(pid)
        if p:
            out.append({"player": p, "teamName": team})
    return out

@app.post("/api/rules", response_model=ScoringRules)
def set_rules(rules: ScoringRules):
    DATA["rules"] = rules.model_dump()
    return rules

@app.post("/api/context", response_model=LeagueContext)
def set_context(ctx: LeagueContext):
    DATA["ctx"] = ctx.model_dump()
    return LeagueContext(**DATA["ctx"])

@app.post("/api/strategy", response_model=StrategyProfile)
def set_strategy(s: StrategyProfile):
    DATA["strategy"] = s.model_dump()
    return StrategyProfile(**DATA["strategy"])

@app.get("/api/suggest_v2", response_model=List[SuggestionV2])
def suggest_v2_endpoint(count: int = 12, pos: Optional[str] = None):
    rules = ScoringRules(**DATA["rules"])
    ctx = LeagueContext(**DATA["ctx"])
    strategy = StrategyProfile(**DATA["strategy"])
    bye_counts = _my_bye_counts()
    all_players = list(DATA["players"].values())

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
