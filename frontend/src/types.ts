export type Player = {
  player_id: number
  name: string
  position: string
  team?: string
  age?: number
  bye_week?: number
  adp?: number
  projected_points?: number
  depth_order?: number
  committee_size?: number
}

export type Suggestion = {
  player: Player
  score: number
  reasons: string[]
}

export type ScoringRules = {
  league_size: number
  roster_qb: number
  roster_rb: number
  roster_wr: number
  roster_te: number
  roster_flex: number
  roster_dst: number
  roster_k: number
  bench: number
  pass_td: number
  pass_yd: number
  pass_int: number
  rush_td: number
  rush_yd: number
  rec_td: number
  rec_yd: number
  ppr: number
  te_premium: number
}

export type LeagueContext = {
  snake: boolean
  teams: number
  pick_slot: number
  round: number
  total_rounds: number
  kdst_gate_round: number
}

