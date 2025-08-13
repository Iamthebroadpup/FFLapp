from typing import Dict, List, Tuple
from models import Player, ScoringRules

def _group(players: List[Player], proj: List[float]) -> Dict[str, List[float]]:
    pos_map: Dict[str, List[float]] = {}
    for p, pts in zip(players, proj):
        pos = (p.position or "").upper()
        pos_map.setdefault(pos, []).append(float(pts))
    for k in pos_map:
        pos_map[k].sort(reverse=True)
    return pos_map

def _base_requirements(rules: ScoringRules) -> Dict[str, int]:
    return {
        "QB": rules.roster_qb,
        "RB": rules.roster_rb,
        "WR": rules.roster_wr,
        "TE": rules.roster_te,
        "DST": rules.roster_dst,
        "K":  rules.roster_k,
    }

def replacement_levels(players: List[Player], proj: List[float], rules: ScoringRules, teams: int) -> Dict[str, float]:
    pos_map = _group(players, proj)
    req = _base_requirements(rules)
    needed: Dict[str, int] = {k: max(0, int(req.get(k, 0) * teams)) for k in ("QB","RB","WR","TE","DST","K")}

    # flex alloc across RB/WR/TE
    flex_slots = max(0, rules.roster_flex) * teams
    ptr = {"RB": needed.get("RB",0), "WR": needed.get("WR",0), "TE": needed.get("TE",0)}
    for _ in range(flex_slots):
        cand: List[Tuple[str, float]] = []
        for pos in ("RB","WR","TE"):
            arr = pos_map.get(pos, [])
            idx = ptr[pos]
            val = arr[idx] if idx < len(arr) else 0.0
            cand.append((pos, val))
        cand.sort(key=lambda x: x[1], reverse=True)
        pick_pos, _ = cand[0]
        needed[pick_pos] = needed.get(pick_pos, 0) + 1
        ptr[pick_pos] += 1

    repl: Dict[str, float] = {}
    for pos, arr in pos_map.items():
        n = needed.get(pos, 0)
        if not arr:
            repl[pos] = 0.0
            continue
        idx = min(max(0, n - 1), len(arr) - 1)
        window = arr[idx: idx + 3] or [arr[idx]]
        repl[pos] = sum(window) / len(window)
    return repl

# export starter requirements for utility
_base_requirements_export = _base_requirements
