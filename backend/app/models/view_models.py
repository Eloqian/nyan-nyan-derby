from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

class PlayerStanding(BaseModel):
    rank: int
    player_id: UUID
    player_name: str
    total_points: int
    wins: int
    matches_played: int
    # history: List[int] # Optional: points per match/race

class StageStandingsResponse(BaseModel):
    stage_id: UUID
    standings: List[PlayerStanding]
