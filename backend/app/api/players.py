from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.services.player_service import PlayerService
from app.models import User
from pydantic import BaseModel

router = APIRouter()

class ClaimRequest(BaseModel):
    qq_id: str
    username: str # Temporary simplified auth simulation

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
    session: AsyncSession = Depends(get_session)
):
    """
    User claims a player by QQ ID.
    In real app, 'username' comes from JWT context.
    """
    # 1. Mock getting current user (User needs to exist first)
    from app.services.user_service import UserService
    user_service = UserService(session)
    user = await user_service.get_by_username(req.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Claim
    player_service = PlayerService(session)
    success = await player_service.claim_player(user, req.qq_id)
    if not success:
        raise HTTPException(status_code=400, detail="Claim failed: Invalid QQ or already claimed")

    return {"message": "Successfully bound QQ to account"}
