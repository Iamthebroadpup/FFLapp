from typing import Dict, List, Any, Tuple
from logic.util import normalize_players  # changed from .util import normalize_players
from models import Player, Suggestion, ScoringRules
from statistics import mean

def _vorp_baseline(players: List[Player], rules: ScoringRules) -> Dict[str, float]:
    by_pos: Dict[str, List[Player]] = {}
    for p in players:
        by_pos.setdefault(p.position, []).append(p)
    for pos in by_pos:
        by_pos[pos].sort(key=lambda x: (-(x.projected_points or 0), x.adp or 9999))

    starters = {
        "QB": rules.league_size * rules.roster_qb,
        "RB": rules.league_size * rules.roster_rb,
        "WR": rules.league_size * rules.roster_wr,
        "TE": rules.league_size * rules.roster_te,
    }
    baselines: Dict[str, float] = {}
    for pos, arr in starters.items():
        pool = by_pos.get(pos, [])
        idx = min(max(arr - 1, 0), max(len(pool)-1, 0))
        window = pool[max(0, idx-2):min(len(pool), idx+3)]
        if window:
            baselines[pos] = mean([(x.projected_points or 0) for x in window])
        else:
            baselines[pos] = 0.0
    return baselines

def _committee_penalty(p: Player) -> float:
    if p.position not in ("RB", "WR"):
        return 0.0
    if p.committee_size is None:
        return 0.0
    if p.committee_size >= 3:
        return 3.0
    if p.committee_size == 2 and (p.depth_order or 99) > 1:
        return 1.5
    return 0.0

def _age_adjustment(p: Player) -> float:
    if p.position == "RB" and p.age and p.age >= 28:
        return -1.5
    if p.position == "WR" and p.age and p.age >= 30:
        return -1.0
    if p.position == "TE" and p.age and p.age <= 24:
        return -0.5
    return 0.0

def _bye_conflict_penalty(p: Player, my_bye_counts: Dict[int, int]) -> float:
    if p.bye_week is None:
        return 0.0
    if my_bye_counts.get(p.bye_week, 0) >= 3:
        return 3.0
    if my_bye_counts.get(p.bye_week, 0) == 2:
        return 1.5
    return 0.0

def score_players(
    undrafted: List[Player],
    my_bye_counts: Dict[int, int],
    rules: ScoringRules
) -> List[Suggestion]:
    baselines = _vorp_baseline(undrafted, rules)
    suggestions: List[Suggestion] = []
    for p in undrafted:
        base = (p.projected_points or 0.0)
        reasons = [f"Base proj: {base:.1f}"]
        vorp = 0.0
        if p.position in baselines:
            vorp = base - baselines[p.position]
            reasons.append(f"VORP vs {p.position} baseline: {vorp:.1f}")

        pen = _committee_penalty(p)
        if pen:
            reasons.append(f"Committee penalty: -{pen:.1f}")

        age_adj = _age_adjustment(p)
        if age_adj:
            reasons.append(f"Age adj: {age_adj:+.1f}")

        bye_pen = _bye_conflict_penalty(p, my_bye_counts)
        if bye_pen:
            reasons.append(f"Bye conflict: -{bye_pen:.1f}")

        adp_bump = 0.0
        if p.adp:
            adp_bump = max(0, (120 - p.adp)) * 0.01
            if adp_bump:
                reasons.append(f"ADP bump: +{adp_bump:.1f}")

        score = base + vorp + adp_bump + age_adj - pen - bye_pen
        suggestions.append(Suggestion(player=p, score=score, reasons=reasons))

    suggestions.sort(key=lambda s: (-s.score, s.player.adp or 9999))
    return suggestions
