from typing import List, Dict, Optional
from models import Player, ScoringRules, SuggestionV2, LeagueContext, StrategyProfile
from logic.engine_v2.reproject import reproject_points
from logic.engine_v2.replacement import replacement_levels, _base_requirements_export
from logic.engine_v2.availability import current_and_next_pick, availability_prob_with_adp, availability_prob_no_adp
from logic.engine_v2.runs import compute_run_pressure, recent_pos_pick_rates
from logic.engine_v2.tiers import compute_tiers_per_player
from logic.engine_v2.normalize import zscore_to_unit

def _market_delta(pick_no: int, p: Player, round_no: int) -> float:
    if p.adp is None: return 0.0
    raw = pick_no - p.adp
    damp = max(0.4, 1.0 - 0.03 * (round_no - 1))
    return max(-20.0, min(20.0, raw * damp))

def _role_certainty_mult(p: Player) -> float:
    mult = 1.0
    if p.committee_size and p.committee_size >= 3: mult *= 0.95
    if p.depth_order and p.depth_order >= 3: mult *= 0.95
    return mult

def _injury_risk(p: Player) -> float:
    s = (p.injury_status or "").upper()
    if s in ("OUT","IR","PUP","SUSPENDED"): return 1.0
    if s in ("QUESTIONABLE","DOUBTFUL"): return 0.6
    return 0.0

def _age_penalty(p: Player) -> float:
    if p.age is None: return 0.0
    pos = (p.position or "").upper()
    a = p.age
    if pos == "RB": return max(0.0, (a - 26) / 10.0)  # small above 26
    if pos == "WR": return max(0.0, (a - 28) / 12.0)
    if pos == "TE": return max(0.0, (a - 28) / 12.0)
    if pos == "QB": return max(0.0, (a - 32) / 14.0)
    return 0.0

def _rookie_volatility(p: Player) -> float:
    if p.years_exp is not None and p.years_exp == 0:
        return 1.0
    return 0.0

def _stack_bonus(p: Player, my_qb_teams: List[str]) -> float:
    if p.position in ("WR","TE") and p.team and p.team in my_qb_teams:
        return 1.0
    return 0.0

def _team_concentration_penalty(p: Player, my_team_counts: Dict[str,int]) -> float:
    if not p.team: return 0.0
    c = my_team_counts.get(p.team, 0)
    # only care about starters later; keep tiny
    return 0.2 * max(0, c - 2)

def _bye_penalty(p: Player, my_bye_counts: Dict[int, int], round_no: int, bench_pick: bool) -> float:
    if not p.bye_week: return 0.0
    overlap = my_bye_counts.get(p.bye_week, 0)
    if overlap <= 2: return 0.0
    base = 0.6 if bench_pick else 1.0
    fade = max(0.3, 1.0 - (round_no - 1) * 0.06)
    return base * (overlap - 2) * fade

def _bench_pick(rules: ScoringRules, my_counts: Dict[str,int]) -> bool:
    req = (rules.roster_qb + rules.roster_rb + rules.roster_wr + rules.roster_te + rules.roster_dst + rules.roster_k + rules.roster_flex)
    have = sum(my_counts.get(p,0) for p in ("QB","RB","WR","TE","DST","K"))
    return have >= req

def suggest_v2(
    players: List[Player],
    drafted: Dict[int, str],
    rules: ScoringRules,
    ctx: LeagueContext,
    my_bye_counts: Dict[int, int],
    strategy: StrategyProfile,
    count: int = 12,
    pos: Optional[str] = None,
    history: Optional[List[Dict]] = None,
    opponents_needs: Optional[Dict[str, Dict[str,int]]] = None,  # teamName -> pos -> remaining starters needed
) -> List[SuggestionV2]:

    pool = [p for p in players if p.player_id not in drafted]
    if pos:
        posu = pos.upper()
        pool = [p for p in pool if (p.position or "").upper() == posu]

    # projections in league scoring
    proj = reproject_points(pool, rules)

    # replacement and VORP
    repl = replacement_levels(pool, proj, rules, ctx.teams)
    vorp_list = []
    for p, pts in zip(pool, proj):
        rpos = (p.position or "").upper()
        vorp_list.append(pts - float(repl.get(rpos, 0.0)))

    # picks + gap
    pick_no, next_pick = current_and_next_pick(ctx)
    picks_gap = max(0, next_pick - pick_no - 1)

    # run pressure + recent rates
    run_press = compute_run_pressure(history or [], window=10, picks_gap=picks_gap)
    pos_rates = recent_pos_pick_rates(history or [], window=10)

    # per-player tiering with adaptive tolerance
    pid_to_tier, pos_to_order, pos_to_pts, tier_heads = compute_tiers_per_player(
        pool, proj, ctx.round, picks_gap, run_press, strategy=strategy.archetype
    )

    # my roster state
    my_ids = {pid for pid, team in drafted.items() if team == "ME"}
    my_players = [p for p in players if p.player_id in my_ids]
    my_qb_teams = [p.team for p in my_players if (p.position or "").upper() == "QB" and p.team]
    my_counts: Dict[str,int] = {}
    my_team_counts: Dict[str,int] = {}
    for p in my_players:
        posp = (p.position or "").upper()
        my_counts[posp] = my_counts.get(posp,0) + 1
        if p.team:
            my_team_counts[p.team] = my_team_counts.get(p.team,0) + 1

    bench_pick = _bench_pick(rules, my_counts)

    # opponents' needs ahead of you
    opp_need_count: Dict[str,int] = {"QB":0,"RB":0,"WR":0,"TE":0,"DST":0,"K":0}
    if opponents_needs:
        # naive: count all opponents (you can refine to only teams picking before you in this round)
        for team, needs in opponents_needs.items():
            for k in opp_need_count:
                opp_need_count[k] += max(0, needs.get(k,0))

    results: List[SuggestionV2] = []

    # precompute means/std for normalization
    import math
    def mean_std(vals: List[float]):
        if not vals: return (0.0, 1.0)
        m = sum(vals)/len(vals)
        s = (sum((v-m)*(v-m) for v in vals)/len(vals))**0.5 or 1.0
        return m, s

    mu_vorp, sd_vorp = mean_std(vorp_list)

    # compute per-candidate features and score
    for idx, (p, pts) in enumerate(zip(pool, proj)):
        posp = (p.position or "").upper()
        vorp = vorp_list[idx]

        # TierGap: estimate drop to best expected at next pick for same pos
        order = pos_to_order.get(posp, [])
        pts_arr = pos_to_pts.get(posp, [])
        try:
            rank = order.index(p.player_id)
        except ValueError:
            rank = 0
        # expected next: subtract expected taken at this position = picks_gap * pos_rates[pos]
        taken = int(round(picks_gap * pos_rates.get(posp, 0.0)))
        idx_next = min(rank + max(0, taken), len(pts_arr) - 1) if pts_arr else 0
        next_best = pts_arr[idx_next] if pts_arr else 0.0
        tier_gap = max(0.0, pts - next_best)

        # Availability: ADP if present else live rates + opponents' needs
        if p.adp is not None:
            survive = availability_prob_with_adp(p, next_pick, pool)
        else:
            survive = availability_prob_no_adp(p, next_pick, pos_rates, opp_need_count, picks_gap)
        can_i_wait = 1.0 - survive  # higher = more urgent

        # Scarcity index: combine tier remaining & position remaining
        # remaining in player's tier:
        tier_id = pid_to_tier.get(p.player_id, 1)
        tier_head_idx, _ = tier_heads.get((posp, tier_id), (0, pts))
        # naive: remaining in tier ~ players after current rank up to before next tier head
        # (approximate by density around rank)
        tier_size_est = max(1, sum(1 for pid in order if pid_to_tier.get(pid,1) == tier_id))
        rank_in_tier = sum(1 for i2 in range(0, rank+1) if pid_to_tier.get(order[i2],1) == tier_id)
        tier_remaining_ratio = max(0.0, (tier_size_est - rank_in_tier) / max(1, tier_size_est))
        # position remaining above replacement: compare rank to replacement index
        # find replacement projection for pos
        repl_val = float(repl.get(posp, 0.0))
        above_rep_total = sum(1 for v in pts_arr if v >= repl_val)
        pos_remaining_ratio = max(0.0, (above_rep_total - (rank+1)) / max(1, above_rep_total))
        # scarcity: 70% tier, 30% pos
        scarcity = 0.7*(1.0 - tier_remaining_ratio) + 0.3*(1.0 - pos_remaining_ratio)

        # Needs & must-fill
        base_req = _base_requirements_export(rules)
        need_raw = max(0, base_req.get(posp, 0) - my_counts.get(posp, 0))
        total_need = sum(max(0, base_req.get(k,0) - my_counts.get(k,0)) for k in base_req) or 1
        need_frac = need_raw / total_need
        must_fill = 0.0
        # soft thresholds: if past 1/3 of draft and still missing starters, escalate
        starters_total = sum(base_req.values()) + rules.roster_flex
        my_starters_have = (my_counts.get("QB",0)+my_counts.get("RB",0)+my_counts.get("WR",0)
                            +my_counts.get("TE",0)+my_counts.get("DST",0)+my_counts.get("K",0))
        draft_progress = (ctx.round-1)/max(1, ctx.total_rounds-1)
        if draft_progress > 0.33 and need_raw > 0:
            must_fill = (draft_progress - 0.33) * 1.5 * need_frac  # grows into late draft

        # Risk & stability
        role_mult = _role_certainty_mult(p)
        injury_risk = _injury_risk(p)
        age_pen = _age_penalty(p)
        rookie_vol = _rookie_volatility(p)
        role_stability = 1.0 - ((1.0 - role_mult) * 0.8)  # convert to bonus in [~0.9..1.0]

        # Handcuff: if RB depth_order==2 and same team as my RB starter(s)
        handcuff = 0.0
        if posp == "RB" and p.depth_order and p.depth_order == 2 and p.team:
            have_rb = any((mp.position or "").upper()=="RB" and mp.team==p.team for mp in my_players)
            if have_rb:
                handcuff = 1.0 * (0.5 + 0.5*injury_risk)

        # Stack & bye & team concentration
        stack = _stack_bonus(p, [t for t in my_qb_teams if t])
        bye_pen = _bye_penalty(p, my_bye_counts, ctx.round, bench_pick)
        team_conc = _team_concentration_penalty(p, my_team_counts)

        # K/DST gate
        kdst_gate = 1.0 if (ctx.round >= ctx.kdst_gate_round or posp not in ("K","DST")) else 0.0

        # Strategy nudges
        if strategy.archetype == "EliteTE" and posp == "TE" and ctx.round <= 4:
            vorp *= 1.08
        if strategy.archetype == "LateQB" and posp == "QB" and ctx.round <= 8:
            vorp *= 0.92
        if strategy.archetype == "ZeroRB" and posp == "RB" and ctx.round <= 3:
            vorp *= 0.9

        # Normalize to [-1..1]
        Z_VORP       = zscore_to_unit(vorp, mu_vorp, sd_vorp)
        Z_TierGap    = zscore_to_unit(tier_gap, 0.0, max(1.0, abs(tier_gap))) if tier_gap>0 else 0.0
        Z_Avail      = (can_i_wait*2.0 - 1.0)  # 0..1 -> -1..1
        Z_Run        = min(1.0, run_press.get(posp, 0.0))  # already >=0
        Z_Scarcity   = (max(0.0, min(1.0, scarcity))*2.0 - 1.0)
        Z_Need       = (need_frac*2.0 - 1.0)
        Z_MustFill   = (max(0.0, min(1.0, must_fill))*2.0 - 1.0)
        Z_Stack      = (stack*2.0 - 1.0) if stack>0 else 0.0
        Z_Bye        = (min(1.0, bye_pen)*2.0 - 1.0) if bye_pen>0 else 0.0
        Z_TeamConc   = (min(1.0, team_conc)*2.0 - 1.0) if team_conc>0 else 0.0
        Z_Injury     = (min(1.0, injury_risk)*2.0 - 1.0) if injury_risk>0 else 0.0
        Z_Age        = (min(1.0, age_pen)*2.0 - 1.0) if age_pen>0 else 0.0
        Z_Role       = ((role_stability-0.9)/0.1) - 1.0  # roughly map ~[0.9..1.0] to [-1..1]
        Z_RookieVol  = (min(1.0, rookie_vol)*2.0 - 1.0) if rookie_vol>0 else 0.0
        Z_Handcuff   = (min(1.0, handcuff)*2.0 - 1.0) if handcuff>0 else 0.0
        Z_Gate       = (kdst_gate*2.0 - 1.0)

        # Round/seat weights
        if ctx.round <= 3:
            W = {"V":1.00,"T":0.35,"A":0.25,"R":0.15,"Sx":0.25,"N":0.20,"F":0.10,"St":0.06,
                 "By":0.12,"Tm":0.05,"In":0.20,"Ag":0.06,"Rl":0.10,"Rv":0.10,"Hc":0.05,"GK":0.30}
        elif ctx.round <= 6:
            W = {"V":0.90,"T":0.30,"A":0.30,"R":0.22,"Sx":0.28,"N":0.22,"F":0.12,"St":0.08,
                 "By":0.10,"Tm":0.06,"In":0.16,"Ag":0.06,"Rl":0.12,"Rv":0.08,"Hc":0.06,"GK":0.35}
        elif ctx.round <= 10:
            W = {"V":0.75,"T":0.25,"A":0.35,"R":0.28,"Sx":0.26,"N":0.22,"F":0.15,"St":0.10,
                 "By":0.08,"Tm":0.06,"In":0.14,"Ag":0.06,"Rl":0.14,"Rv":0.06,"Hc":0.10,"GK":0.45}
        else:
            W = {"V":0.60,"T":0.18,"A":0.35,"R":0.30,"Sx":0.24,"N":0.18,"F":0.18,"St":0.12,
                 "By":0.06,"Tm":0.06,"In":0.10,"Ag":0.06,"Rl":0.16,"Rv":0.04,"Hc":0.14,"GK":0.60}

        # Bench tweaks
        if _bench_pick(rules, my_counts):
            W["Rv"] *= 0.8   # less penalty for rookies late
            W["In"] *= 0.9   # slightly less injury-averse
            W["St"] *= 1.1   # slightly more okay with stacking/upside

        score = (
            W["V"]*Z_VORP + W["T"]*Z_TierGap + W["A"]*Z_Avail + W["R"]*Z_Run + W["Sx"]*Z_Scarcity
            + W["N"]*Z_Need + W["F"]*Z_MustFill + W["St"]*Z_Stack
            - W["By"]*Z_Bye - W["Tm"]*Z_TeamConc - W["In"]*Z_Injury - W["Ag"]*Z_Age
            + W["Rl"]*Z_Role - W["Rv"]*Z_RookieVol + W["Hc"]*Z_Handcuff + W["GK"]*Z_Gate
        )

        comps = {
            "Proj": round(pts,1),
            "VORPz": round(Z_VORP,3),
            "TierGap": round(tier_gap,2),
            "AvailZ": round(Z_Avail,3),
            "RunPress": round(min(1.0, run_press.get(posp,0.0)),3),
            "ScarcityZ": round(Z_Scarcity,3),
            "NeedZ": round(Z_Need,3),
            "MustFillZ": round(Z_MustFill,3),
            "Stack": round(Z_Stack,3),
            "ByeZ": round(Z_Bye,3),
            "TeamConcZ": round(Z_TeamConc,3),
            "InjuryZ": round(Z_Injury,3),
            "AgeZ": round(Z_Age,3),
            "RoleZ": round(Z_Role,3),
            "RookieZ": round(Z_RookieVol,3),
            "HandcuffZ": round(Z_Handcuff,3),
        }

        reasons = [f"VORP strong" if Z_VORP>0 else "VORP modest"]
        if Z_TierGap>0.2: reasons.append("Tier cliff if you wait")
        if Z_Avail>0.2: reasons.append("Low survival to next pick")
        if run_press.get(posp,0.0)>0.2: reasons.append(f"{posp} run detected")
        if Z_MustFill>0.2: reasons.append("Must-fill starter")
        if Z_Stack>0: reasons.append("Stack bonus")
        if Z_Bye>0: reasons.append("Bye overlap")
        if Z_Injury>0.2: reasons.append("Injury risk")
        if Z_Handcuff>0.2: reasons.append("Handcuff value")

        results.append(SuggestionV2(player=p, score=float(score), components=comps, reasons=reasons))

    results.sort(key=lambda s: s.score, reverse=True)
    return results[:max(1, min(count, 40))]
