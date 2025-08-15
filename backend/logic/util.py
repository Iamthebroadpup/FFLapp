from typing import Dict, List, Any, Optional
from models import Player

# ---- Simple scoring fallback if feed points are missing ----
def _points_from_statline(stat: dict) -> float:
    """
    Very simple default (0.5 PPR) if FantasyPoints/FantasyPointsPPR not provided by feed.
    """
    return (
        (stat.get("PassingYards", 0) * 0.04)
        + (stat.get("PassingTouchdowns", 0) * 4)
        + (stat.get("Interceptions", 0) * -2)
        + (stat.get("RushingYards", 0) * 0.1)
        + (stat.get("RushingTouchdowns", 0) * 6)
        + (stat.get("Receptions", 0) * 0.5)
        + (stat.get("ReceivingYards", 0) * 0.1)
        + (stat.get("ReceivingTouchdowns", 0) * 6)
        - (stat.get("FumblesLost", 0) * 2)
    )


def _coerce_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def normalize_players(raw: Dict[str, Any]) -> Dict[int, Player]:
    """
    Build a map of PlayerID -> Player (pydantic model) using all available
    feed artifacts: players, byes, depth charts, projections, injuries,
    and (fallback) last-season statlines.
    """
    # 1) Seed players from the "players" master list
    players: Dict[int, Player] = {}

    for p in raw.get("players", []):
        pid = p.get("PlayerID")
        if pid is None:
            continue
        pid = int(pid)

        name = p.get("Name") or p.get("ShortName") or (p.get("FirstName", "") + " " + p.get("LastName", ""))
        pos = (p.get("Position") or "").upper()
        team = p.get("Team")
        age = _coerce_float(p.get("Age"))

        players[pid] = Player(
            player_id=pid,
            name=(name or "").strip(),
            position=pos,
            team=team,
            age=age if age is not None else None,
            bye_week=None,
            adp=None,
            projected_points=None,
            depth_order=None,
            committee_size=None,
        )

    # 2) Attach bye weeks if present
    bye_map: Dict[str, int] = {}
    for b in raw.get("byes", []):
        t = b.get("Team")
        wk = b.get("ByeWeek", b.get("Week"))
        if t and isinstance(wk, int):
            bye_map[t] = wk

    for p in players.values():
        if p.team and p.team in bye_map:
            p.bye_week = bye_map[p.team]

    # 3) Depth
    for d in raw.get("depth", []):
        pid = d.get("PlayerID")
        if pid is None:
            continue
        pid = int(pid)
        if pid not in players:
            continue
        depth_order = d.get("DepthOrder")
        try:
            if depth_order is not None:
                players[pid].depth_order = int(depth_order)
        except Exception:
            pass

    # 4) Committee sizes
    team_pos_counts: Dict[str, Dict[str, int]] = {}
    for p in players.values():
        if not p.team or not p.position:
            continue
        team_pos_counts.setdefault(p.team, {})
        team_pos_counts[p.team].setdefault(p.position, 0)
        team_pos_counts[p.team][p.position] += 1

    for p in players.values():
        if p.team and p.position and p.team in team_pos_counts and p.position in team_pos_counts[p.team]:
            p.committee_size = team_pos_counts[p.team][p.position]

    # 5) Projections + ADP
    for proj in raw.get("projections", []):
        pid = proj.get("PlayerID")
        if pid is None:
            continue
        pid = int(pid)
        if pid not in players:
            continue

        # ---- Projected Points ----
        fp = proj.get("FantasyPointsPPR")
        if fp is None:
            fp = proj.get("FantasyPoints")
        if fp is None:
            fp = _points_from_statline(proj)
        fpf = _coerce_float(fp)
        if fpf is not None:
            players[pid].projected_points = fpf

        # ---- ADP ----
        adp = proj.get("AverageDraftPositionPPR") or proj.get("AverageDraftPosition") or proj.get("ADP")
        adpf = _coerce_float(adp)
        if adpf is not None and adpf > 0:
            players[pid].adp = adpf

        # ---- Per-stat backfill for reproject_points ----
        try:
            if getattr(players[pid], "passing_yards", None) is None:
                players[pid].passing_yards = _coerce_float(proj.get("PassingYards"))
                players[pid].passing_tds = _coerce_float(proj.get("PassingTouchdowns"))
                players[pid].interceptions = _coerce_float(proj.get("Interceptions"))
                players[pid].rushing_yards = _coerce_float(proj.get("RushingYards"))
                players[pid].rushing_tds = _coerce_float(proj.get("RushingTouchdowns"))
                players[pid].receptions = _coerce_float(proj.get("Receptions"))
                players[pid].receiving_yards = _coerce_float(proj.get("ReceivingYards"))
                players[pid].receiving_tds = _coerce_float(proj.get("ReceivingTouchdowns"))
                players[pid].fumbles_lost = _coerce_float(proj.get("FumblesLost"))
        except Exception:
            pass

    # 6) Fallback: last season stats
    for stat in raw.get("season_stats", []):
        pid = stat.get("PlayerID")
        if pid is None:
            continue
        pid = int(pid)
        if pid not in players:
            continue

        if players[pid].projected_points is None:
            players[pid].projected_points = _points_from_statline(stat)

        try:
            if getattr(players[pid], "passing_yards", None) is None:
                players[pid].passing_yards = _coerce_float(stat.get("PassingYards"))
                players[pid].passing_tds = _coerce_float(stat.get("PassingTouchdowns"))
                players[pid].interceptions = _coerce_float(stat.get("Interceptions"))
                players[pid].rushing_yards = _coerce_float(stat.get("RushingYards"))
                players[pid].rushing_tds = _coerce_float(stat.get("RushingTouchdowns"))
                players[pid].receptions = _coerce_float(stat.get("Receptions"))
                players[pid].receiving_yards = _coerce_float(stat.get("ReceivingYards"))
                players[pid].receiving_tds = _coerce_float(stat.get("ReceivingTouchdowns"))
                players[pid].fumbles_lost = _coerce_float(stat.get("FumblesLost"))
        except Exception:
            pass

    # 7) Filter to fantasy positions
    filtered = {
        pid: p for pid, p in players.items()
        if (p.position or "") in ("QB", "RB", "WR", "TE", "K", "DST")
    }
    return filtered
