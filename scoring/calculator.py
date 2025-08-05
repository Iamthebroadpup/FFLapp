from .rules import ScoringRules


def calculate_points(stats: dict, rules: ScoringRules) -> float:
    """Calculate fantasy points from a stats dictionary."""
    s = stats
    r = rules
    points = 0.0
    points += s.get("receptions", 0) * r.points_per_reception
    points += s.get("passing_tds", 0) * r.passing_td
    points += s.get("rushing_tds", 0) * r.rushing_td
    points += s.get("receiving_tds", 0) * r.receiving_td
    points += s.get("passing_yards", 0) * r.passing_yards
    points += s.get("rushing_yards", 0) * r.rushing_yards
    points += s.get("receiving_yards", 0) * r.receiving_yards
    points += s.get("interceptions", 0) * r.interception
    return points
