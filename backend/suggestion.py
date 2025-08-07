from collections import defaultdict

POS = {"QB","RB","WR","TE","K","DST"}

def compute_vor(ranks: list[dict], roster: dict[str,int], teams: int):
    proj_by_pos = defaultdict(list)
    cleaned = []

    for p in ranks:
        pos = p.get("position")
        if pos not in POS:
            continue
        pts = p.get("proj_fp") or p.get("projected_points") or 0
        item = {
            "player_id": p.get("player_id"),
            "name": p.get("name"),
            "team": p.get("team"),
            "pos": pos,
            "proj": float(pts or 0),
        }
        cleaned.append(item)
        proj_by_pos[pos].append(item)

    # replacement line at each position
    replacement = {}
    for pos, arr in proj_by_pos.items():
        arr.sort(key=lambda x: x["proj"], reverse=True)
        starters_per_team = max(roster.get(pos, 0), 0)
        idx = max(starters_per_team * teams - 1, 0)
        replacement[pos] = arr[idx]["proj"] if arr else 0.0

    for item in cleaned:
        item["vor"] = item["proj"] - replacement.get(item["pos"], 0.0)

    cleaned.sort(key=lambda x: (x["vor"], x["proj"]), reverse=True)
    return cleaned
