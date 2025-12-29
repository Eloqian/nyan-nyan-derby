from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, JSON
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

# Enums
class TournamentStatus(str, Enum):
    SETUP = "setup"
    ACTIVE = "active"
    COMPLETED = "completed"

class StageType(str, Enum):
    ROUND_ROBIN = "round_robin" # for Groups
    ELIMINATION = "elimination" # for Bracket
    DOUBLE_ELIMINATION = "double_elimination"

class MatchStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    FINISHED = "finished"

# Models
class Tournament(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    name: str
    status: TournamentStatus = Field(default=TournamentStatus.SETUP)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    stages: List["Stage"] = Relationship(back_populates="tournament")

class Stage(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    tournament_id: UUID = Field(foreign_key="tournament.id")
    name: str
    stage_type: StageType
    sequence_order: int # 1, 2, 3...

    # Stores scoring rules (e.g. {"1st": 9, "bonus": ...})
    rules_config: Dict[str, Any] = Field(default={}, sa_type=JSON)

    tournament: Tournament = Relationship(back_populates="stages")
    groups: List["Group"] = Relationship(back_populates="stage")

class Group(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    stage_id: UUID = Field(foreign_key="stage.id")
    name: str # "Group A"

    stage: Stage = Relationship(back_populates="groups")
    matches: List["Match"] = Relationship(back_populates="group")

class Match(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    group_id: UUID = Field(foreign_key="group.id")
    name: Optional[str] = None # e.g. "Upper Bracket R1 M1"
    start_time: Optional[datetime] = None
    status: MatchStatus = Field(default=MatchStatus.PENDING)

    group: Group = Relationship(back_populates="matches")
    participants: List["MatchParticipant"] = Relationship(back_populates="match")
    races: List["Race"] = Relationship(back_populates="match")

class MatchParticipant(SQLModel, table=True):
    match_id: UUID = Field(foreign_key="match.id", primary_key=True)
    player_id: UUID = Field(foreign_key="player.id", primary_key=True)

    # Optional override if this slot is specifically an NPC (even if player isn't)
    # But usually we rely on player.is_npc

    match: Match = Relationship(back_populates="participants")
    player: "Player" = Relationship(back_populates="matches")

class Race(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    match_id: UUID = Field(foreign_key="match.id")
    race_number: int # 1, 2, 3...

    match: Match = Relationship(back_populates="races")
    results: List["RaceResult"] = Relationship(back_populates="race")

class RaceResult(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    race_id: UUID = Field(foreign_key="race.id")
    player_id: UUID = Field(foreign_key="player.id")
    rank: int # 1, 2, 3... (Raw rank before NPC shift)

    # Computed points for this single race (can be cached here or calculated on fly)
    points_awarded: int = 0

    race: Race = Relationship(back_populates="results")
    player: "Player" = Relationship(back_populates="race_results")

from .user import Player
