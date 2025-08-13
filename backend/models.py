from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

class ScoringRules(BaseModel):
    league_size: int = 12
    roster_qb: int = 1
    roster_rb: int = 2
    roster_wr: int = 2
    roster_te: int = 1
    roster_flex: int = 1
    roster_dst: int = 1
    roster_k: int = 1
    bench: int = 5

    pass_td: float = 4.0
    pass_yd: float = 0.04
    pass_int: float = -2.0
    rush_td: float = 6.0
    rush_yd: float = 0.1
    rec_td: float = 6.0
    rec_yd: float = 0.1
    ppr: float = 0.5
    te_premium: float = 0.0

class Player(BaseModel):
    player_id: int
    name: str
    position: str
    team: Optional[str] = None
    age: Optional[int] = None
    years_exp: Optional[int] = None
    bye_week: Optional[int] = None
    adp: Optional[float] = None
    projected_points: Optional[float] = None
    depth_order: Optional[int] = None
    committee_size: Optional[int] = None

    # per-stat projections
    passing_yards: Optional[float] = None
    passing_tds: Optional[float] = None
    interceptions: Optional[float] = None
    rushing_yards: Optional[float] = None
    rushing_tds: Optional[float] = None
    receptions: Optional[float] = None
    receiving_yards: Optional[float] = None
    receiving_tds: Optional[float] = None
    fumbles_lost: Optional[float] = None
    two_pt_conversions: Optional[float] = None

    # risk/injury
    injury_status: Optional[str] = None   # e.g., Questionable/Out/IR/PUP/Suspended
    recent_injuries: Optional[int] = None # simple count if available

class Suggestion(BaseModel):
    player: "Player"
    score: float
    reasons: List[str] = []

class InitSummary(BaseModel):
    players_count: int = 0
    depth_teams: int = 0
    bye_count: int = 0

class LeagueContext(BaseModel):
    season: int = 2025
    snake: bool = True
    teams: int = 12
    pick_slot: int = 1
    round: int = 1
    total_rounds: int = 16
    kdst_gate_round: int = 12  # gate K/DST until this round

class StrategyProfile(BaseModel):
    archetype: Literal["Balanced","ZeroRB","HeroRB","AnchorWR","EliteTE","LateQB"] = "Balanced"
    risk: Literal["conservative","balanced","aggressive"] = "balanced"

class SuggestionV2(BaseModel):
    player: "Player"
    score: float
    components: Dict[str, float] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)
