from typing import Dict, List

BASELINE_SHARE = {"RB":0.30,"WR":0.38,"QB":0.12,"TE":0.12,"DST":0.04,"K":0.04}

def compute_run_pressure(history: List[dict], window: int, picks_gap: int) -> Dict[str, float]:
    if window <= 0 or not history:
        return {k: 0.0 for k in BASELINE_SHARE}
    recent = history[-window:]
    counts: Dict[str, int] = {}
    total = 0
    for h in recent:
        pos = str(h.get("pos") or "").upper()
        counts[pos] = counts.get(pos, 0) + 1
        total += 1
    out: Dict[str, float] = {}
    for pos, base in BASELINE_SHARE.items():
        share = (counts.get(pos, 0) / total) if total else 0.0
        delta = max(0.0, share - base)
        gap_amp = 1.0 + min(1.0, picks_gap / 12.0) * 0.5
        out[pos] = delta / max(0.01, base) * gap_amp
    return out

def recent_pos_pick_rates(history: List[dict], window: int) -> Dict[str, float]:
    if window <= 0 or not history:
        return {k: BASELINE_SHARE[k] for k in BASELINE_SHARE}
    recent = history[-window:]
    counts: Dict[str, int] = {}
    for h in recent:
        pos = str(h.get("pos") or "").upper()
        counts[pos] = counts.get(pos, 0) + 1
    total = sum(counts.values()) or 1
    return {pos: counts.get(pos,0)/total for pos in BASELINE_SHARE}
