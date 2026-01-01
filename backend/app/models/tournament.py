from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, JSON
from sqlalchemy import Text, Column
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
    start_time: Optional[datetime] = None

    # General configuration for the tournament (e.g. seed_ratio: 0.1)
    rules_config: Dict[str, Any] = Field(default={}, sa_type=JSON)
    
    # Detailed prize pool configuration
    prize_pool_config: Dict[str, Any] = Field(default={}, sa_type=JSON)
    
    # The full text content of the rules/announcement
    rules_content: Optional[str] = Field(default=None, sa_column=Column(Text))

    stages: List["Stage"] = Relationship(back_populates="tournament")
    participants: List["TournamentParticipant"] = Relationship(back_populates="tournament")

class TournamentParticipant(SQLModel, table=True):
    tournament_id: UUID = Field(foreign_key="tournament.id", primary_key=True)
    player_id: UUID = Field(foreign_key="player.id", primary_key=True)
    
    checked_in: bool = Field(default=False)
    checked_in_at: Optional[datetime] = None
    
    # Per-tournament seed level if we want to override global
    seed_level: int = Field(default=0)

    tournament: Tournament = Relationship(back_populates="participants")
    player: "Player" = Relationship(back_populates="tournament_participations")

class Stage(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    tournament_id: UUID = Field(foreign_key="tournament.id")
    name: str
    stage_type: StageType
    sequence_order: int # 1, 2, 3...

    # Stores scoring rules (e.g. {"1st": 9, "bonus": ...})
    rules_config: Dict[str, Any] = Field(default={}, sa_type=JSON)

    # Configuration for progression, specifically wildcards (e.g. {"wildcard_count": 12, "strategy": "global_best_losers"})
    wildcard_rules: Dict[str, Any] = Field(default={}, sa_type=JSON)

    tournament: Tournament = Relationship(back_populates="stages")
    groups: List["Group"] = Relationship(back_populates="stage")

class Group(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    stage_id: UUID = Field(foreign_key="stage.id")
    name: str # "Group A"

    stage: Stage = Relationship(back_populates="groups")
    matches: List["Match"] = Relationship(back_populates="group")
    participants: List["GroupParticipant"] = Relationship(back_populates="group")

class GroupParticipant(SQLModel, table=True):
    group_id: UUID = Field(foreign_key="group.id", primary_key=True)
    player_id: UUID = Field(foreign_key="player.id", primary_key=True)

    group: Group = Relationship(back_populates="participants")
    player: "Player" = Relationship(back_populates="groups")

class Match(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    group_id: UUID = Field(foreign_key="group.id")
    name: Optional[str] = None # e.g. "Upper Bracket R1 M1"
    start_time: Optional[datetime] = None
    status: MatchStatus = Field(default=MatchStatus.PENDING)
    host_player_id: Optional[UUID] = Field(default=None, foreign_key="player.id")
    
    # User input room number for the game
    room_number: Optional[str] = None

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

from .user import User, Player
from .tournament import Tournament, Stage, Group, Match, MatchParticipant, Race, RaceResult, GroupParticipant, TournamentParticipant
