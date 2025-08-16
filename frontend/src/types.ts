export type Projections = {
  passing_yards: number; passing_tds: number; interceptions: number;
  rushing_yards: number; rushing_tds: number;
  receptions: number; receiving_yards: number; receiving_tds: number;
  fumbles_lost: number; two_pt: number;
  fg_made: number; xp_made: number;
}

export type DSTProjections = {
  sacks: number; interceptions: number; fumbles_recovered: number; safeties: number;
  def_tds: number; return_tds: number; points_allowed: number;
}

export type Player = {
  player_id: number;
  name: string;
  team?: string | null;
  position: 'QB'|'RB'|'WR'|'TE'|'K'|'DST'|'DEF'|string;
  bye_week?: number | null;
  adp?: number | null;
  adp_ppr?: number | null;
  projections: Projections;
  dst?: DSTProjections | null;
}

export type PlayerScore = {
  player: Player;
  points: number;
  vorp: number;
  rank: number;
  value_vs_adp?: number | null;
}

export type Suggestion = {
  player_score: PlayerScore;
  reason: string;
}

export type LeagueConfig = {
  season_year: number;
  season_type: 'REG'|'PRE'|'POST';
  teams: number;
  roster: Record<string, number>;
  scoring: {
    pass_yd: number; pass_td: number; pass_int: number;
    rush_yd: number; rush_td: number;
    rec: number; rec_yd: number; rec_td: number;
    fum_lost: number; two_pt: number;
    k_fg: number; k_xp: number;
    dst_sack: number; dst_int: number; dst_fr: number; dst_safety: number;
    dst_td: number; dst_ret_td: number;
    dst_pa_0: number; dst_pa_1_6: number; dst_pa_7_13: number;
    dst_pa_14_20: number; dst_pa_21_27: number; dst_pa_28_34: number; dst_pa_35p: number;
  }
}
