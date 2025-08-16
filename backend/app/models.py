from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class Projections(BaseModel):
    # Offensive + K projections
    passing_yards: float = 0
    passing_tds: float = 0
    interceptions: float = 0
    rushing_yards: float = 0
    rushing_tds: float = 0
    receptions: float = 0
    receiving_yards: float = 0
    receiving_tds: float = 0
    fumbles_lost: float = 0
    two_pt: float = 0
    # Kicker
    fg_made: float = 0
    xp_made: float = 0

class DSTProjections(BaseModel):
    sacks: float = 0
    interceptions: float = 0
    fumbles_recovered: float = 0
    safeties: float = 0
    def_tds: float = 0
    return_tds: float = 0
    points_allowed: float = 21  # expected points allowed

class Player(BaseModel):
    player_id: int
    name: str
    team: Optional[str] = None
    position: str
    bye_week: Optional[int] = None
    adp: Optional[float] = None
    adp_ppr: Optional[float] = None
    projections: Projections = Projections()
    dst: Optional[DSTProjections] = None

class ScoringWeights(BaseModel):
    # offense
    pass_yd: float = 0.04
    pass_td: float = 4.0
    pass_int: float = -2.0
    rush_yd: float = 0.1
    rush_td: float = 6.0
    rec: float = 0.5
    rec_yd: float = 0.1
    rec_td: float = 6.0
    fum_lost: float = -2.0
    two_pt: float = 2.0
    # kicker
    k_fg: float = 3.0
    k_xp: float = 1.0
    # defense (per-event weights)
    dst_sack: float = 1.0
    dst_int: float = 2.0
    dst_fr: float = 2.0
    dst_safety: float = 2.0
    dst_td: float = 6.0
    dst_ret_td: float = 6.0
    # points allowed buckets (exact NFL default per SportsDataIO docs)
    dst_pa_0: float = 10.0
    dst_pa_1_6: float = 7.0
    dst_pa_7_13: float = 4.0
    dst_pa_14_20: float = 1.0
    dst_pa_21_27: float = 0.0
    dst_pa_28_34: float = -1.0
    dst_pa_35p: float = -4.0

class LeagueConfig(BaseModel):
    season_year: int = Field(..., ge=2000, le=2100)
    season_type: str = Field(default="REG", pattern=r"^(REG|POST|PRE)$")
    teams: int = 12
    roster: Dict[str, int] = Field(
        default_factory=lambda: {"QB":1,"RB":2,"WR":2,"TE":1,"FLEX":1,"DST":1,"K":1}
    )
    scoring: ScoringWeights = ScoringWeights()

class PlayerScore(BaseModel):
    player: Player
    points: float
    vorp: float
    rank: int
    value_vs_adp: Optional[float] = None

class InitSummary(BaseModel):
    players_count: int
    with_adp: int
    season: str

class Suggestion(BaseModel):
    player_score: PlayerScore
    reason: str

class SuggestRequest(BaseModel):
    drafted_ids: List[int] = []
    other_drafted_ids: List[int] = []
    config: LeagueConfig = LeagueConfig(season_year=2025)
    user_team_index: int | None = None
    current_pick_overall: int | None = None
    snake: bool = True
    rounds: int | None = None

class DraftPick(BaseModel):
    overall_pick: int
    team_index: int
    player_id: int

class DraftState(BaseModel):
    picks: List[DraftPick] = []
