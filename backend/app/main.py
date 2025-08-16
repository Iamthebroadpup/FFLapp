from __future__ import annotations
import os, math
from typing import List, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv, find_dotenv

from .sportsdata import (
    fetch_projections_and_adp_and_dst,
    normalize_player,
    normalize_dst,
    merge_adp,
    SportsDataError,
)
from .models import (
    LeagueConfig, InitSummary, Player, PlayerScore,
    SuggestRequest, Suggestion, ScoringWeights,
    DraftState, DraftPick
)
from .cache import GLOBAL_CACHE
class _Scoring: ...
from .scoring import fantasy_points, compute_vorp

# Robust .env load regardless of working directory
load_dotenv(find_dotenv())

app = FastAPI(title="DraftHelper API", version="1.4")

# --- CORS ---
origins = (os.getenv("CORS_ORIGINS") or "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_KEY = "players"
DRAFT_KEY = "draft_state"


@app.get("/api/health")
def health():
    return {"ok": True}


# Optional: quick env check to debug .env visibility
@app.get("/api/debug/env")
def debug_env():
    import pathlib
    from dotenv import find_dotenv
    return {
        "cwd": str(pathlib.Path().resolve()),
        "env_path": find_dotenv(),
        "has_key": bool(os.getenv("SPORTSDATAIO_API_KEY")),
        "base": os.getenv("SPORTSDATAIO_BASE"),
    }


@app.get("/api/init", response_model=InitSummary)
async def api_init(
    season: int = Query(..., ge=2000, le=2100),
    season_type: str = Query("REG", pattern="^(REG|PRE|POST)$"),
):
    try:
        proj_rows, adp_rows, dst_rows = await fetch_projections_and_adp_and_dst(season, season_type)
    except SportsDataError as e:
        raise HTTPException(500, f"SportsData fetch failed: {e}")
    except Exception as e:
        raise HTTPException(500, f"SportsData fetch failed: {e}")

    players_map: Dict[int, Dict] = {}

    # Include QB/RB/WR/TE/K from the player projections feed
    for r in proj_rows:
        p = normalize_player(r)
        if p["position"] in ("QB", "RB", "WR", "TE", "K"):
            players_map[p["player_id"]] = p

    # Add DST rows from the DST projections feed
    for r in dst_rows or []:
        p = normalize_dst(r)
        if p.get("player_id"):
            players_map[p["player_id"]] = p

    # Merge ADP (includes K and often DST)
    if adp_rows:
        merge_adp(players_map, adp_rows)

    players = [Player(**p) for p in players_map.values()]
    GLOBAL_CACHE.set(DATA_KEY, players)
    GLOBAL_CACHE.set(DRAFT_KEY, DraftState(picks=[]))

    with_adp = sum(1 for p in players if p.adp or p.adp_ppr)
    return InitSummary(players_count=len(players), with_adp=with_adp, season=f"{season}{season_type}")


@app.get("/api/draft/state", response_model=DraftState)
def api_draft_state():
    st: DraftState | None = GLOBAL_CACHE.get(DRAFT_KEY)
    if not st:
        st = DraftState(picks=[])
        GLOBAL_CACHE.set(DRAFT_KEY, st)
    return st


@app.post("/api/draft/pick", response_model=DraftState)
def api_draft_pick(pick: DraftPick):
    st: DraftState | None = GLOBAL_CACHE.get(DRAFT_KEY)
    if not st:
        st = DraftState(picks=[])
    st.picks.append(pick)
    GLOBAL_CACHE.set(DRAFT_KEY, st)
    return st


@app.post("/api/draft/undo", response_model=DraftState)
def api_draft_undo():
    st: DraftState | None = GLOBAL_CACHE.get(DRAFT_KEY)
    if not st or not st.picks:
        st = st or DraftState(picks=[])
        return st
    st.picks.pop()
    GLOBAL_CACHE.set(DRAFT_KEY, st)
    return st


@app.post("/api/draft/clear", response_model=DraftState)
def api_draft_clear():
    st = DraftState(picks=[])
    GLOBAL_CACHE.set(DRAFT_KEY, st)
    return st


@app.get("/api/players", response_model=List[PlayerScore])
def api_players(
    teams: int = 12,
    # offense
    scoring_pass_yd: float = 0.04, scoring_pass_td: float = 4, scoring_pass_int: float = -2,
    scoring_rush_yd: float = 0.1, scoring_rush_td: float = 6,
    scoring_rec: float = 0.5, scoring_rec_yd: float = 0.1, scoring_rec_td: float = 6,
    scoring_fum_lost: float = -2, scoring_two_pt: float = 2,
    # kicker
    scoring_k_fg: float = 3, scoring_k_xp: float = 1,
    # dst
    scoring_dst_sack: float = 1, scoring_dst_int: float = 2, scoring_dst_fr: float = 2, scoring_dst_safety: float = 2,
    scoring_dst_td: float = 6, scoring_dst_ret_td: float = 6,
    scoring_dst_pa_0: float = 10, scoring_dst_pa_1_6: float = 7, scoring_dst_pa_7_13: float = 4,
    scoring_dst_pa_14_20: float = 1, scoring_dst_pa_21_27: float = 0, scoring_dst_pa_28_34: float = -1, scoring_dst_pa_35p: float = -4,
    # roster
    roster_qb: int = 1, roster_rb: int = 2, roster_wr: int = 2, roster_te: int = 1, roster_flex: int = 1,
    roster_dst: int = 1, roster_k: int = 1,
):
    players: List[Player] = GLOBAL_CACHE.get(DATA_KEY)
    if not players:
        raise HTTPException(400, "No data loaded. Call /api/init first.")

    weights = ScoringWeights(
        pass_yd=scoring_pass_yd, pass_td=scoring_pass_td, pass_int=scoring_pass_int,
        rush_yd=scoring_rush_yd, rush_td=scoring_rush_td,
        rec=scoring_rec, rec_yd=scoring_rec_yd, rec_td=scoring_rec_td,
        fum_lost=scoring_fum_lost, two_pt=scoring_two_pt,
        k_fg=scoring_k_fg, k_xp=scoring_k_xp,
        dst_sack=scoring_dst_sack, dst_int=scoring_dst_int, dst_fr=scoring_dst_fr, dst_safety=scoring_dst_safety,
        dst_td=scoring_dst_td, dst_ret_td=scoring_dst_ret_td,
        dst_pa_0=scoring_dst_pa_0, dst_pa_1_6=scoring_dst_pa_1_6, dst_pa_7_13=scoring_dst_pa_7_13,
        dst_pa_14_20=scoring_dst_pa_14_20, dst_pa_21_27=scoring_dst_pa_21_27,
        dst_pa_28_34=scoring_dst_pa_28_34, dst_pa_35p=scoring_dst_pa_35p,
    )
    roster = {
        "QB": roster_qb, "RB": roster_rb, "WR": roster_wr, "TE": roster_te,
        "FLEX": roster_flex, "DST": roster_dst, "K": roster_k
    }

    pts_list = [(p, fantasy_points(p, weights)) for p in players]
    vorp_map = compute_vorp(pts_list, roster, teams)

    enriched: List[PlayerScore] = []
    for p, pts in pts_list:
        vorp = vorp_map.get(p.player_id, 0.0)
        enriched.append(PlayerScore(player=p, points=round(pts, 2), vorp=round(vorp, 2), rank=0))

    enriched.sort(key=lambda x: x.points, reverse=True)
    for i, ps in enumerate(enriched, start=1):
        ps.rank = i
        if ps.player.adp:
            ps.value_vs_adp = i - ps.player.adp
        elif ps.player.adp_ppr:
            ps.value_vs_adp = i - ps.player.adp_ppr

    return enriched


@app.post("/api/suggest", response_model=List[Suggestion])
def api_suggest(req: SuggestRequest):
    """
    Suggests players based on VORP + projected points, positional need, ADP edge, snake risk,
    and a bye-week crowding penalty (applies to *your* team only).

    Bye-week penalty:
      - No penalty until you already have > 2 players with the same bye (i.e., adding a 3rd starts the penalty).
      - Penalty grows quadratically with crowding so that picking a 5th becomes effectively untenable.
    """
    def picks_until_next(user_idx: int, current_overall: int, teams: int, snake: bool, rounds: int | None = None) -> int:
        if user_idx is None or current_overall is None or user_idx < 1 or teams < 1 or current_overall < 1:
            return 0
        r = math.ceil(current_overall / teams)
        pos_in_round = current_overall - (r - 1) * teams
        your_pos = user_idx if (not snake or r % 2 == 1) else (teams - user_idx + 1)
        if your_pos > pos_in_round:
            return your_pos - pos_in_round
        nxt = (teams - pos_in_round) + (user_idx if ((r + 1) % 2 == 1 or not snake) else (teams - user_idx + 1))
        return nxt

    players: List[Player] = GLOBAL_CACHE.get(DATA_KEY)
    if not players:
        raise HTTPException(400, "No data loaded. Call /api/init first.")

    # Combine server-side picks with client-provided lists (both sides remove players from pool)
    st: DraftState | None = GLOBAL_CACHE.get(DRAFT_KEY)
    server_drafted = set([dp.player_id for dp in (st.picks if st else [])])
    merged_drafted = set(req.drafted_ids) | set(req.other_drafted_ids) | server_drafted

    # Map for quick lookup by id
    players_by_id: Dict[int, Player] = {p.player_id: p for p in players}

    # --- Bye-week crowding context: only your team matters for this penalty ---
    user_drafted = set(req.drafted_ids)
    bye_counts: Dict[int, int] = {}
    for pid in user_drafted:
        pl = players_by_id.get(pid)
        if pl and pl.bye_week:
            bye_counts[pl.bye_week] = bye_counts.get(pl.bye_week, 0) + 1

    # Tuning: no penalty until >2 with same bye; then quadratic growth.
    BYE_FREE_LIMIT = 2            # 0..2 have no penalty; 3rd starts penalty
    BYE_UNIT = 5.0                # base severity; quadratic growth makes 5th near-untenable
    # crowd=1 (adding 3rd):  -5
    # crowd=2 (adding 4th):  -20
    # crowd=3 (adding 5th):  -45  <-- strong
    # crowd=4 (adding 6th):  -80  <-- basically a no-go

    weights = req.config.scoring
    pts_list = [(p, fantasy_points(p, weights)) for p in players if p.player_id not in merged_drafted]
    vorp_map = compute_vorp(pts_list, req.config.roster, req.config.teams)

    max_need = max(req.config.roster.values() or [1])

    def need_mult(pos: str) -> float:
        n = req.config.roster.get("DST" if pos == "DEF" else pos, 0)
        return 1.0 + (n / max_need) * 0.15

    N = picks_until_next(req.user_team_index or 0, req.current_pick_overall or 0, req.config.teams, bool(req.snake), req.rounds)
    rows: list[tuple] = []
    for p, pts in pts_list:
        mult = need_mult(p.position)
        vorp = vorp_map.get(p.player_id, 0.0)

        # ADP "value" bump
        adp_edge = 0.0
        adp_val = p.adp_ppr or p.adp
        if adp_val:
            adp_edge = max(0.0, (adp_val - 50) / 200.0)

        # Snake risk bonus (nudges players likely to be gone before your next turn)
        risk_edge = 0.0
        if adp_val and N > 0 and req.current_pick_overall:
            if adp_val <= req.current_pick_overall + N:
                risk_edge = 0.30
            elif adp_val <= req.current_pick_overall + int(1.5 * N):
                risk_edge = 0.15

        # Bye-week penalty (applies only against *your* current bye stacks)
        bye_pen = 0.0
        if getattr(p, "bye_week", None):
            have = bye_counts.get(p.bye_week, 0)
            if have > BYE_FREE_LIMIT:
                crowd = have - BYE_FREE_LIMIT + 1  # 1 when you'd be adding the 4th? careful:
                # Explanation:
                # have is how many you ALREADY roster with that bye.
                # if have == 2 -> adding would be 3rd => start penalty with crowd=1
                # if have == 3 -> adding 4th => crowd=2
                # if have == 4 -> adding 5th => crowd=3 (strong)
                bye_pen = BYE_UNIT * (crowd ** 2)

        score = (vorp * 0.85 + pts * 0.15) * mult + adp_edge + risk_edge - bye_pen
        reason = (
            f"{p.position} | VORP {vorp:.1f}, Proj {pts:.1f}, need x{mult:.2f}"
            + (f", ADP ~{adp_val:.0f}" if adp_val else "")
            + (f", risk +{risk_edge:.2f}" if risk_edge > 0 else "")
            + (f", bye wk {p.bye_week} crowd -{bye_pen:.1f}" if bye_pen > 0 else "")
        )
        rows.append((score, p, pts, vorp, reason))

    rows.sort(key=lambda x: x[0], reverse=True)

    out: List[Suggestion] = []
    for i, row in enumerate(rows[:24], start=1):
        # tolerant unpack (in case of old hot-reload tuples)
        score, p, pts, vorp = row[:4]
        reason = row[4] if len(row) > 4 else ""
        out.append(
            Suggestion(
                player_score=PlayerScore(
                    player=p,
                    points=round(pts, 2),
                    vorp=round(vorp, 2),
                    rank=i,
                    value_vs_adp=((i - (p.adp_ppr or p.adp)) if (p.adp_ppr or p.adp) else None),
                ),
                reason=reason,
            )
        )

    return out
