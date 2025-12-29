from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.services.tournament_service import TournamentService
from pydantic import BaseModel
from typing import List

router = APIRouter()

class RaceResultInput(BaseModel):
    race_number: int
    rankings: List[str] # List of Player UUIDs

@router.post("/{match_id}/result")
async def record_result(
    match_id: str,
    input_data: RaceResultInput,
    session: AsyncSession = Depends(get_session)
):
    service = TournamentService(session)
    results = await service.record_race_result(match_id, input_data.race_number, input_data.rankings)
    return {"message": "Results recorded", "count": len(results)}
