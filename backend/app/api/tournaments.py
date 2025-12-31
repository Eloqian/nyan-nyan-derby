from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.models.tournament import Tournament, TournamentStatus, Stage, StageType
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class TournamentCreate(BaseModel):
    name: str
    rules_config: Dict[str, Any] = {} # e.g. {"points_map": {...}, "prizes": [...]}
    stages_config: List[Dict[str, Any]] = [] # Optional initial stages setup

class TournamentUpdate(BaseModel):
    status: Optional[TournamentStatus] = None
    name: Optional[str] = None
    rules_config: Optional[Dict[str, Any]] = None

@router.post("/", response_model=Tournament)
async def create_tournament(
    t_data: TournamentCreate,
    session: AsyncSession = Depends(get_session)
):
    # 1. Create Tournament
    tourney = Tournament(
        name=t_data.name,
        status=TournamentStatus.SETUP,
        rules_config=t_data.rules_config
    )
    session.add(tourney)
    await session.commit()
    await session.refresh(tourney)
    
    # 2. Create Default Stages if provided (Simplified)
    # Typically we might want separate endpoints, but basic skeleton is good.
    if t_data.stages_config:
        for i, s_cfg in enumerate(t_data.stages_config):
            stage = Stage(
                tournament_id=tourney.id,
                name=s_cfg.get("name", f"Stage {i+1}"),
                stage_type=s_cfg.get("stage_type", StageType.ROUND_ROBIN),
                sequence_order=i+1,
                rules_config=s_cfg.get("rules_config", {})
            )
            session.add(stage)
        await session.commit()

    return tourney

@router.get("/current", response_model=Optional[Tournament])
async def get_current_tournament(session: AsyncSession = Depends(get_session)):
    """
    Get the most recent active or setup tournament.
    """
    # Priority: Active > Setup > Completed (by created_at desc)
    # Simple logic: order by status priority? Or just latest created.
    # Let's get latest created for now.
    stmt = select(Tournament).order_by(Tournament.created_at.desc()) # type: ignore
    result = await session.exec(stmt)
    return result.first()

@router.patch("/{tournament_id}", response_model=Tournament)
async def update_tournament(
    tournament_id: str,
    update_data: TournamentUpdate,
    session: AsyncSession = Depends(get_session)
):
    tourney = await session.get(Tournament, tournament_id)
    if not tourney:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    if update_data.name is not None:
        tourney.name = update_data.name
    if update_data.status is not None:
        tourney.status = update_data.status
    if update_data.rules_config is not None:
        # Deep merge or replace? Replace for simplicity.
        tourney.rules_config = update_data.rules_config
        
    session.add(tourney)
    await session.commit()
    await session.refresh(tourney)
    return tourney
