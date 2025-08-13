from typing import Dict, List, Tuple
from models import Player

# Base relative drop (percent) by position
BASE_DROP = {"RB":0.075,"WR":0.075,"TE":0.10,"QB":0.12,"DST":0.15,"K":0.15}

def _sort_pos(players: List[Player], proj: List[float]):
    pos_lists: Dict[str, List[Tuple[int, float]]] = {}
    for p, pts in zip(players, proj):
        pos = (p.position or "").upper()
        pos_lists.setdefault(pos, []).append((p.player_id, float(pts)))
    for pos in pos_lists:
        pos_lists[pos].sort(key=lambda x: x[1], reverse=True)
    return pos_lists

def _local_stats(arr: List[float], i: int, n: int = 3) -> Tuple[float, float]:
    # avg & simple range proxy of next n gaps
    start = i
    end = min(len(arr)-1, i+n)
    gaps = []
    for k in range(start, end):
        prev, cur = arr[k], arr[k+1]
        if prev <= 1e-6: continue
        gaps.append((prev - cur) / prev)
    if not gaps:
        return 0.0, 0.0
    avg = sum(gaps)/len(gaps)
    rng = (max(gaps) - min(gaps)) if len(gaps) >= 2 else 0.0
    return avg, rng

def compute_tiers_per_player(
    players: List[Player],
    proj: List[float],
    round_no: int,
    picks_gap: int,
    run_pressure: Dict[str, float],
    tier_min_size: Dict[str, int] = None,
    strategy: str = "Balanced",
) -> Tuple[Dict[int,int], Dict[str,List[int]], Dict[str,List[float]], Dict[Tuple[str,int],Tuple[int,float]]]:
    """
    Returns: pid_to_tier, pos_to_order, pos_to_pts, tier_heads
    Uses a per-player tolerance τ_i that adapts to local neighborhood, uncertainty proxy, supply, timing, strategy.
    """
    if tier_min_size is None:
        tier_min_size = {"RB":3,"WR":3,"TE":3,"QB":2,"DST":2,"K":2}

    pos_lists = _sort_pos(players, proj)
    pid_to_tier: Dict[int,int] = {}
    pos_to_order: Dict[str,List[int]] = {}
    pos_to_pts: Dict[str,List[float]] = {}
    tier_heads: Dict[Tuple[str,int],Tuple[int,float]] = {}

    # simple uncertainty proxy (role) from player model
    role_uncertainty: Dict[int, float] = {}
    for p in players:
        u = 0.0
        if p.committee_size and p.committee_size >= 3: u += 0.5
        if p.depth_order and p.depth_order >= 3: u += 0.5
        if p.years_exp is not None and p.years_exp == 0: u += 0.2
        if (p.injury_status or "").upper() in ("OUT","IR","PUP","SUSPENDED","QUESTIONABLE"):
            u += 0.5
        role_uncertainty[p.player_id] = min(1.0, u)

    for pos, arr in pos_lists.items():
        pts = [v for _, v in arr]
        order = [pid for pid, _ in arr]
        pos_to_order[pos] = order
        pos_to_pts[pos] = pts
        if not order:
            continue

        base = BASE_DROP.get(pos, 0.1)
        tier = 1
        tier_heads[(pos, tier)] = (0, pts[0])
        pid_to_tier[order[0]] = tier

        start_idx = 0
        for i in range(len(order)-1):
            # build per-player tolerance τ_i
            avg_gap, rng = _local_stats(pts, i, n=3)
            # neighborhood
            neigh = 0.85 if (avg_gap > base and rng > 0.02) else (1.15 if avg_gap < base/2 else 1.0)
            # uncertainty from player i
            unc = 0.9 + 0.15 * role_uncertainty.get(order[i], 0.0)  # 0.9..1.05
            unc = max(0.9, min(1.05, unc))
            # supply proxy: plenty left in current segment vs not (use position share remaining)
            remaining = len(order) - (i+1)
            supply = 1.15 if remaining > 8 else (1.0 if remaining > 4 else 0.9)
            # timing: long wrap & run → split easier
            runp = run_pressure.get(pos, 0.0)
            timing = 0.95 if (picks_gap >= 10 and runp > 0.2) else (1.05 if picks_gap <= 2 and runp < 0.05 else 1.0)
            # strategy
            strat = 1.0
            if strategy == "EliteTE" and pos == "TE" and round_no <= 4: strat = 0.95
            if strategy == "ZeroRB" and pos == "RB" and round_no <= 3: strat = 1.05

            tau = base * neigh * unc * supply * timing * strat
            # actual local drop
            if pts[i] <= 1e-6:
                gap = 0.0
            else:
                gap = (pts[i] - pts[i+1]) / pts[i]

            # apply minimum tier size guard
            min_size = tier_min_size.get(pos, 2)
            current_size = (i - start_idx + 1)
            if gap >= tau and current_size >= min_size:
                tier += 1
                tier_heads[(pos, tier)] = (i+1, pts[i+1])
                start_idx = i+1
            pid_to_tier[order[i+1]] = tier

    return pid_to_tier, pos_to_order, pos_to_pts, tier_heads
