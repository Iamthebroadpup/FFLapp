from dataclasses import dataclass


@dataclass
class ScoringRules:
    """Standard scoring options for fantasy football."""

    points_per_reception: float = 1.0
    passing_td: float = 4.0
    rushing_td: float = 6.0
    receiving_td: float = 6.0
    passing_yards: float = 0.04
    rushing_yards: float = 0.1
    receiving_yards: float = 0.1
    interception: float = -2.0
    fumble: float = -2.0
    two_point_conv: float = 2.0
    field_goal_made: float = 3.0
    extra_point: float = 1.0
