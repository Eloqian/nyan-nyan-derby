from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, JSON, AutoString
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import EmailStr

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: Optional[EmailStr] = Field(default=None, index=True, sa_type=AutoString)
    avatar_url: Optional[str] = Field(default=None)
    is_admin: bool = False

class User(UserBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str

    players: List["Player"] = Relationship(back_populates="user")

class PlayerBase(SQLModel):
    in_game_name: str
    qq_id: str = Field(index=True, unique=True)
    is_npc: bool = False

class Player(PlayerBase, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="user.id")

    # Seeding Logic: 0 = None, 1 = Group Head, 2 = Skip Audition
    seed_level: int = Field(default=0)

    # Cache for aggregated stats (e.g., {"first_place_count": 5})
    # This allows efficient tie-breaking without complex joins every time
    stats: Dict[str, Any] = Field(default={}, sa_type=JSON)

    user: Optional[User] = Relationship(back_populates="players")
    matches: List["MatchParticipant"] = Relationship(back_populates="player")
    groups: List["GroupParticipant"] = Relationship(back_populates="player")
    race_results: List["RaceResult"] = Relationship(back_populates="player")
    tournament_participations: List["TournamentParticipant"] = Relationship(back_populates="player")

from .tournament import MatchParticipant, RaceResult, GroupParticipant, TournamentParticipant
