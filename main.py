"""Example usage of the fantasy football helper modules."""
from backend.nfl_data import get_play_by_play
from scoring.rules import ScoringRules
from scoring.calculator import calculate_points


def main() -> None:
    try:
        pbp = get_play_by_play(2023)
        print("Loaded", len(pbp), "plays")
    except Exception as exc:  # pragma: no cover - network error handling
        print("Could not load play-by-play:", exc)

    rules = ScoringRules(points_per_reception=1.0)
    example_stats = {
        "receptions": 5,
        "receiving_yards": 80,
        "receiving_tds": 1,
    }
    pts = calculate_points(example_stats, rules)
    print("Example points:", pts)


if __name__ == "__main__":
    main()
