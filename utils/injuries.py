def flag_injury_risk(injury_report: dict) -> bool:
    """Simple heuristic to flag players with risky injury status."""
    status = injury_report.get("status", "").lower()
    return status in {"q", "d", "o", "questionable", "doubtful", "out"}
