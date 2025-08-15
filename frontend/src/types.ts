// frontend/src/types.ts

export type Player = {
  player_id: number;
  name: string;
  position: string;
  team?: string | null;
  age?: number | null;
  bye_week?: number | null;
  adp?: number | null;
  projected_points?: number | null;
  depth_order?: number | null;
  committee_size?: number | null;
};

export type Suggestion = {
  player: Player;
  score: number;
  components?: Record<string, number>;
  reasons?: string[];
};

export type ScoringRules = {
  league_size: number;
  roster_qb: number;
  roster_rb: number;
  roster_wr: number;
  roster_te: number;
  roster_flex: number;
  roster_dst: number;
  roster_k: number;
  bench: number;

  pass_td: number;
  pass_yd: number;
  pass_int: number;

  rush_td: number;
  rush_yd: number;

  rec_td: number;
  rec_yd: number;
  ppr: number;
  te_premium: number;
};
