from typing import Dict, List, Any, Optional
from models import Player

def _points_from_statline(stat: dict) -> float:
    """
    Very simple default (0.5 PPR) if FantasyPoints not provided by feed.
    """
    return (
        (stat.get("PassingYards", 0) * 0.04)
        + (stat.get("PassingTouchdowns", 0) * 4)
        + (stat.get("Interceptions", 0) * -2)
        + (stat.get("RushingYards", 0) * 0.1)
        + (stat.get("RushingTouchdowns", 0) * 6)
        + (stat.get("ReceivingYards", 0) * 0.1)
        + (stat.get("ReceivingTouchdowns", 0) * 6)
        + (stat.get("Receptions", 0) * 0.5)
        - (stat.get("FumblesLost", 0) * 2)
    )

def normalize_players(raw) -> Dict[int, Player]:
    players: Dict[int, Player] = {}

    # Base player identities
    for r in raw.get("players", []):
        pid = int(r.get("PlayerID"))
        players[pid] = Player(
            player_id=pid,
            name=f"{r.get('FirstName','').strip()} {r.get('LastName','').strip()}".strip(),
            position=r.get("Position", ""),
            team=r.get("Team"),
            age=r.get("Age"),
            years_exp=r.get("Experience"),
        )

    # Injuries
    for inj in raw.get("injuries", []):
        try:
            pid = int(inj.get("PlayerID"))
        except Exception:
            continue
        if pid in players:
            players[pid].injury_status = inj.get("Status") or inj.get("PracticeStatus")

    # Bye weeks
    byes = raw.get("byes", [])
    for b in byes:
        team = b.get("Team")
        bye_week = b.get("Week")
        if team and bye_week:
            for p in players.values():
                if p.team == team:
                    p.bye_week = bye_week

    # Depth charts (depth order & committee size)
    depth = raw.get("depth", [])
    team_pos_counts: Dict[str, Dict[str, int]] = {}
    for d in depth:
        team = d.get("Team")
        position = d.get("Position")
        chart = d.get("DepthChart", [])
        if not team or not position:
            continue
        team_pos_counts.setdefault(team, {}).setdefault(position, 0)
        count = 0
        for c in chart:
            pid = c.get("PlayerID")
            if pid:
                count += 1
                pid = int(pid)
                if pid in players:
                    players[pid].depth_order = c.get("DepthOrder")
        team_pos_counts[team][position] = count

    for p in players.values():
        if p.team and p.position and p.team in team_pos_counts and p.position in team_pos_counts[p.team]:
            p.committee_size = team_pos_counts[p.team][p.position]

    # Projections with ADP (best case)
    for proj in raw.get("projections", []):
        pid = proj.get("PlayerID")
        if pid is None:
            continue
        pid = int(pid)
        if pid not in players:
            continue

        # keep per-stat if present
        players[pid].passing_yards = proj.get("PassingYards")
        players[pid].passing_tds   = proj.get("PassingTouchdowns")
        players[pid].interceptions = proj.get("Interceptions")
        players[pid].rushing_yards = proj.get("RushingYards")
        players[pid].rushing_tds   = proj.get("RushingTouchdowns")
        players[pid].receptions    = proj.get("Receptions")
        players[pid].receiving_yards = proj.get("ReceivingYards")
        players[pid].receiving_tds   = proj.get("ReceivingTouchdowns")
        players[pid].fumbles_lost    = proj.get("FumblesLost")
        players[pid].two_pt_conversions = proj.get("TwoPointConversionPasses", 0) + proj.get("TwoPointConversionRuns", 0) + proj.get("TwoPointConversionReceptions", 0)

        fp = proj.get("FantasyPoints")
        if fp is None:
            fp = _points_from_statline(proj)
        players[pid].projected_points = float(fp)

        adp = proj.get("AverageDraftPosition") or proj.get("ADP") or proj.get("AverageDraftPositionPPR")
        if adp:
            try:
                players[pid].adp = float(adp)
            except Exception:
                pass

    # Fallback: previous season stats -> compute projected_points if still missing
    for stat in raw.get("season_stats", []):
        pid = stat.get("PlayerID")
        if pid is None:
            continue
        pid = int(pid)
        if pid not in players:
            continue
        if players[pid].projected_points is None:
            players[pid].projected_points = float(_points_from_statline(stat))

        # if we never set per-stat, fill what we can
        players[pid].passing_yards = players[pid].passing_yards or stat.get("PassingYards")
        players[pid].passing_tds   = players[pid].passing_tds   or stat.get("PassingTouchdowns")
        players[pid].interceptions = players[pid].interceptions or stat.get("Interceptions")
        players[pid].rushing_yards = players[pid].rushing_yards or stat.get("RushingYards")
        players[pid].rushing_tds   = players[pid].rushing_tds   or stat.get("RushingTouchdowns")
        players[pid].receptions    = players[pid].receptions    or stat.get("Receptions")
        players[pid].receiving_yards = players[pid].receiving_yards or stat.get("ReceivingYards")
        players[pid].receiving_tds   = players[pid].receiving_tds   or stat.get("ReceivingTouchdowns")
        players[pid].fumbles_lost    = players[pid].fumbles_lost    or stat.get("FumblesLost")

    # Filter to fantasy-relevant positions
    filtered = {pid: p for pid, p in players.items() if p.position in ("QB", "RB", "WR", "TE", "K", "DST")}
    return filtered
