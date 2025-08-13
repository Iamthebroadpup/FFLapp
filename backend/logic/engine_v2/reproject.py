from typing import List
from models import Player, ScoringRules

def _v(v):
    return float(v or 0.0)

def reproject_points(players: List[Player], rules: ScoringRules) -> List[float]:
    out: List[float] = []
    for p in players:
        pos = (p.position or "").upper()
        pts = 0.0
        pts += _v(p.passing_yards)   * rules.pass_yd
        pts += _v(p.passing_tds)     * rules.pass_td
        pts += _v(p.interceptions)   * rules.pass_int
        pts += _v(p.rushing_yards)   * rules.rush_yd
        pts += _v(p.rushing_tds)     * rules.rush_td
        pts += _v(p.receiving_yards) * rules.rec_yd
        pts += _v(p.receiving_tds)   * rules.rec_td
        pts += _v(p.receptions)      * rules.ppr
        if pos == "TE" and rules.te_premium:
            pts += _v(p.receptions) * rules.te_premium
        pts += -2.0 * _v(p.fumbles_lost)
        pts +=  2.0 * _v(p.two_pt_conversions)

        if pos in ("K","DST") and (pts == 0.0) and (p.projected_points is not None):
            pts = float(p.projected_points)
        if pts == 0.0 and p.projected_points is not None:
            pts = float(p.projected_points)

        # light role/committee dampening
        if p.committee_size and p.committee_size >= 3:
            pts *= 0.98
        if p.depth_order and p.depth_order >= 3:
            pts *= 0.97
        out.append(max(0.0, pts))
    return out
