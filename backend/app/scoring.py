from __future__ import annotations
from typing import Dict, List, Tuple
from .models import Player, ScoringWeights

def _dst_points_allowed_bucket(pa: float, w: ScoringWeights) -> float:
    if pa <= 0: return w.dst_pa_0
    if pa <= 6: return w.dst_pa_1_6
    if pa <= 13: return w.dst_pa_7_13
    if pa <= 20: return w.dst_pa_14_20
    if pa <= 27: return w.dst_pa_21_27
    if pa <= 34: return w.dst_pa_28_34
    return w.dst_pa_35p

def fantasy_points(p: Player, w: ScoringWeights) -> float:
    # DST
    if p.position in ("DST", "DEF") and p.dst:
        d = p.dst
        return (
            d.sacks * w.dst_sack
            + d.interceptions * w.dst_int
            + d.fumbles_recovered * w.dst_fr
            + d.safeties * w.dst_safety
            + d.def_tds * w.dst_td
            + d.return_tds * w.dst_ret_td
            + _dst_points_allowed_bucket(d.points_allowed, w)
        )

    # Kicker
    if p.position == "K":
        pr = p.projections
        return pr.fg_made * w.k_fg + pr.xp_made * w.k_xp

    # Offensive player
    pr = p.projections
    return (
        pr.passing_yards * w.pass_yd
        + pr.passing_tds * w.pass_td
        + pr.interceptions * w.pass_int
        + pr.rushing_yards * w.rush_yd
        + pr.rushing_tds * w.rush_td
        + pr.receptions * w.rec
        + pr.receiving_yards * w.rec_yd
        + pr.receiving_tds * w.rec_td
        + pr.fumbles_lost * w.fum_lost
        + pr.two_pt * w.two_pt
    )

def replacement_counts(roster: Dict[str,int], teams: int) -> Dict[str,int]:
    flex = roster.get("FLEX", 0)
    base = {k:v for k,v in roster.items() if k != "FLEX"}
    base["RB"] = base.get("RB",0) + round(flex*0.5)
    base["WR"] = base.get("WR",0) + round(flex*0.4)
    base["TE"] = base.get("TE",0) + (flex - round(flex*0.5) - round(flex*0.4))
    needed = {pos: cnt*teams for pos, cnt in base.items() if pos in ("QB","RB","WR","TE","K","DST","DEF")}
    return needed

def compute_vorp(players: List[Tuple[Player,float]], roster: Dict[str,int], teams: int) -> Dict[int, float]:
    by_pos: Dict[str, List[Tuple[int,float]]] = {}
    for player, pts in players:
        pos = "DST" if player.position == "DEF" else player.position
        by_pos.setdefault(pos, []).append((player.player_id, pts))

    needed = replacement_counts(roster, teams)
    vorp: Dict[int, float] = {}
    for pos, arr in by_pos.items():
        arr.sort(key=lambda x: x[1], reverse=True)
        rep_index = max(0, min(len(arr)-1, needed.get(pos, 0)-1))
        rep_pts = arr[rep_index][1] if arr else 0.0
        for pid, pts in arr:
            vorp[pid] = pts - rep_pts
    return vorp
