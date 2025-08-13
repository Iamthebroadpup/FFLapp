from typing import List, Dict
from statistics import mean, pstdev

def zscore_to_unit(x: float, mu: float, sigma: float, cap: float = 2.0) -> float:
    if sigma <= 1e-9:
        z = 0.0
    else:
        z = (x - mu) / sigma
    z = max(-cap, min(cap, z))
    # map [-cap..cap] -> [-1..1]
    return z / cap

def minmax_to_unit(x: float, lo: float, hi: float) -> float:
    if hi - lo <= 1e-9:
        return 0.0
    v = (x - lo) / (hi - lo)
    return max(0.0, min(1.0, v)) * 2.0 - 1.0

def normalize_list(values: List[float]) -> List[float]:
    if not values:
        return []
    mu = mean(values)
    s = pstdev(values) or 1.0
    return [zscore_to_unit(v, mu, s) for v in values]
