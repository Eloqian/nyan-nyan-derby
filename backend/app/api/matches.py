from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.services.tournament_service import TournamentService
from pydantic import BaseModel
from typing import List
from uuid import UUID

router = APIRouter()

class PlayerRank(BaseModel):
    player_id: UUID
    rank: int

class RaceResultInput(BaseModel):
    race_number: int
    rankings: List[PlayerRank] # Explicit rank mapping

@router.post("/{match_id}/result")
async def record_result(
    match_id: str,
    input_data: RaceResultInput,
    session: AsyncSession = Depends(get_session)
):
    service = TournamentService(session)
    # Pass the list of PlayerRank objects directly to the service
    results = await service.record_race_result(match_id, input_data.race_number, input_data.rankings)
    return {"message": "Results recorded", "count": len(results)}
