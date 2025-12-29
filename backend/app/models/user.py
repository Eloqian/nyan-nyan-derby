from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import EmailStr

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: Optional[EmailStr] = Field(default=None, index=True)
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

    # Metadata for roster import (e.g. initial seed info)
    # Stored as generic JSON if needed, or specific columns.
    # For now, keeping it simple.

    user: Optional[User] = Relationship(back_populates="players")
    matches: List["MatchParticipant"] = Relationship(back_populates="player")
    race_results: List["RaceResult"] = Relationship(back_populates="player")

from .tournament import MatchParticipant, RaceResult
