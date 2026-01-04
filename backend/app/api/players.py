from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
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

class CreatePlayerRequest(BaseModel):
    in_game_name: str
    qq_id: str

@router.post("/", status_code=201)
async def create_player(
    req: CreatePlayerRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin only: Manually create a player.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
        
    service = PlayerService(session)
    existing = await service.get_player_by_qq(req.qq_id)
    if existing:
        raise HTTPException(status_code=400, detail="Player with this QQ ID already exists")
        
    player = await service.create_player(req.in_game_name, req.qq_id)
    return player

@router.post("/import", status_code=201)
async def import_roster(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin only: Import roster CSV.
    Checks for duplicates. If found, returns 409 with details.
    """
    content = await file.read()
    
    try:
        decoded = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            decoded = content.decode('gb18030')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid file encoding. Please use UTF-8 or GBK.")

    service = PlayerService(session)
    result = await service.validate_roster_csv(decoded)
    
    if result['conflicts']:
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Duplicate entries found in file",
                "conflicts": result['conflicts'],
                "valid": result['valid']
            }
        )
    
    # If no conflicts, proceed to save valid records immediately
    count = await service.batch_create_players(result['valid'])
    return {"message": f"Imported {count} new players"}

@router.post("/batch", status_code=201)
async def batch_create_players(
    players: List[CreatePlayerRequest],
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin only: Batch create players (used after resolving conflicts).
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
            
        service = PlayerService(session)
        # Convert Pydantic models to dicts
        data = [p.dict() for p in players]
        count = await service.batch_create_players(data)
        return {"message": f"Imported {count} players"}
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(error_msg) # Print to stdout
        # Write to a log file for the agent to read
        with open("backend_error.log", "w", encoding="utf-8") as f:
            f.write(error_msg)
        # Return the error to the client
        raise HTTPException(status_code=400, detail=f"Server Error: {str(e)}")

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
