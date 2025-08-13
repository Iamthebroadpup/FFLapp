from typing import Tuple, List, Dict
import math
from statistics import pstdev
from models import LeagueContext, Player

SIGMA_BY_POS_DEFAULT = {"QB":10.0,"RB":12.0,"WR":14.0,"TE":10.0,"DST":8.0,"K":8.0}

def current_and_next_pick(ctx: LeagueContext) -> Tuple[int, int]:
    t = ctx.teams
    if ctx.snake:
        if ctx.round % 2 == 1:
            pick = (ctx.round - 1) * t + ctx.pick_slot
            nxt  = ctx.round * t + (t - ctx.pick_slot + 1)
        else:
            pick = (ctx.round - 1) * t + (t - ctx.pick_slot + 1)
            nxt  = ctx.round * t + ctx.pick_slot
    else:
        pick = (ctx.round - 1) * t + ctx.pick_slot
        nxt  = ctx.round * t + ctx.pick_slot
    return pick, nxt

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _adaptive_sigma(pos: str, pool: List[Player]) -> float:
    adps = sorted([float(p.adp) for p in pool if p.adp is not None and (p.position or "").upper() == pos])
    if len(adps) < 8:
        return SIGMA_BY_POS_DEFAULT.get(pos, 12.0)
    return max(6.0, min(20.0, pstdev(adps) or SIGMA_BY_POS_DEFAULT.get(pos, 12.0)))

def availability_prob_with_adp(p: Player, next_pick: int, pool: List[Player]) -> float:
    pos = (p.position or "").upper()
    adp = float(p.adp or 999.0)
    sigma = _adaptive_sigma(pos, pool)
    z = (next_pick - adp) / sigma
    return max(0.0, min(1.0, norm_cdf(z)))

def availability_prob_no_adp(
    p: Player,
    next_pick: int,
    recent_pos_pick_rates: Dict[str, float],
    opponents_need_counts: Dict[str, int],
    picks_gap: int
) -> float:
    """
    Estimate survive probability using only live room signals.
    """
    pos = (p.position or "").upper()
    # weight recent pick rate by opponents' needs share
    total_need = sum(opponents_need_counts.values()) or 1
    need_share = opponents_need_counts.get(pos, 0) / total_need
    rate = recent_pos_pick_rates.get(pos, 0.0)
    rate = 0.6 * rate + 0.4 * need_share
    expected_taken = max(0.0, picks_gap * rate)
    # crude survival: if many expected taken at this pos, survival falls
    # map expected_taken to [0..1] with a soft curve (more picks -> lower survive)
    survive = 1.0 / (1.0 + expected_taken)
    return max(0.0, min(1.0, survive))
