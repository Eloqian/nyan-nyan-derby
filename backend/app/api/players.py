from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.services.player_service import PlayerService
from app.models import User, Player
from app.api.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

class ClaimRequest(BaseModel):
    qq_id: str

@router.post("/import", status_code=201)
async def import_roster(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin only: Import roster CSV.
    Format: in_game_name,qq_id,is_npc
    """
    content = await file.read()
    service = PlayerService(session)
    count = await service.import_roster_from_csv(content.decode('utf-8'))
    return {"message": f"Imported {count} new players"}

@router.post("/claim")
async def claim_player(
    req: ClaimRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    User claims a player by QQ ID.
    Authenticated User only.
    """
    player_service = PlayerService(session)
    success = await player_service.claim_player(current_user, req.qq_id)
    if not success:
        raise HTTPException(status_code=400, detail="Claim failed: Invalid QQ or already claimed")

    return {"message": "Successfully bound QQ to account"}

@router.get("/", response_model=List[Player])
async def list_players(
    claimed: bool = False,
    session: AsyncSession = Depends(get_session)
):
    """
    List players. Option to filter by 'claimed' (has user_id).
    """
    stmt = select(Player)
    if claimed:
        stmt = stmt.where(Player.user_id != None)
    
    # Sort by claimed first, then name
    stmt = stmt.order_by(Player.user_id.desc(), Player.in_game_name)
    result = await session.exec(stmt)
    return result.all()
