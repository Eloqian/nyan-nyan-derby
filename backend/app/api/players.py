from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.responses import JSONResponse
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.services.player_service import PlayerService
from app.models import User, Player
from app.models.tournament import TournamentParticipant
from app.api.auth import get_current_user
from pydantic import BaseModel
from uuid import UUID

router = APIRouter()

class ClaimRequest(BaseModel):
    qq_id: str

class CreatePlayerRequest(BaseModel):
    in_game_name: str
    qq_id: str

class PlayerUpdate(BaseModel):
    in_game_name: Optional[str] = None
    qq_id: Optional[str] = None

class PlayerResponse(BaseModel):
    id: UUID
    in_game_name: str
    qq_id: str
    user_id: Optional[UUID] = None
    is_npc: bool = False
    checked_in: bool = False
    joined_tournament: bool = False

@router.post("/", status_code=201)
async def create_player(
    req: CreatePlayerRequest,
    tournament_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin only: Manually create a player.
    Optional: Pass tournament_id to auto-check-in the player to that tournament.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
        
    service = PlayerService(session)
    existing = await service.get_player_by_qq(req.qq_id)
    if existing:
        # Check if we should add to tournament even if exists
        if tournament_id:
             await service._add_to_tournament(existing.id, tournament_id)
             await session.commit()
             return existing
        raise HTTPException(status_code=400, detail="Player with this QQ ID already exists")
        
    player = await service.create_player(req.in_game_name, req.qq_id, tournament_id)
    return player

@router.post("/import", status_code=201)
async def import_roster(
    file: UploadFile = File(...),
    tournament_id: Optional[UUID] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin only: Import roster CSV.
    Checks for duplicates. If found, returns 409 with details.
    Optional: Pass tournament_id to auto-check-in players.
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
    count = await service.batch_create_players(result['valid'], tournament_id)
    return {"message": f"Imported {count} new players"}

@router.post("/batch", status_code=201)
async def batch_create_players(
    players: List[CreatePlayerRequest],
    tournament_id: Optional[UUID] = None,
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
        count = await service.batch_create_players(data, tournament_id)
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

@router.get("/me", response_model=PlayerResponse)
async def get_my_player_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get the player profile bound to the current user.
    """
    stmt = select(Player).where(Player.user_id == current_user.id)
    result = await session.exec(stmt)
    player = result.first()
    
    if not player:
        raise HTTPException(status_code=404, detail="No player profile bound")
        
    return player

@router.get("/", response_model=List[PlayerResponse])
async def list_players(
    claimed: bool = False,
    q: Optional[str] = None,
    tournament_id: Optional[UUID] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    List players. Option to filter by 'claimed' (has user_id) or search query 'q'.
    If 'tournament_id' is provided, includes 'checked_in' status for that tournament.
    """
    if tournament_id:
        # Left Join to get checked_in status AND participation status
        # We select Player and the whole Participant object (or specific fields)
        stmt = select(Player, TournamentParticipant).outerjoin(
            TournamentParticipant, 
            (Player.id == TournamentParticipant.player_id) & 
            (TournamentParticipant.tournament_id == tournament_id)
        )
    else:
        # Just Player, checked_in will be False by default logic below
        stmt = select(Player)

    if claimed:
        stmt = stmt.where(Player.user_id != None)
    
    if q:
        stmt = stmt.where(
            or_(
                Player.in_game_name.contains(q),
                Player.qq_id.contains(q)
            )
        )
    
    # Sort by claimed first, then name
    stmt = stmt.order_by(Player.user_id.desc(), Player.in_game_name)
    
    if tournament_id:
        results = await session.exec(stmt)
        response = []
        for player, participant in results:
            p_dict = player.dict()
            if participant:
                p_dict['joined_tournament'] = True
                p_dict['checked_in'] = True if participant.checked_in else False
            else:
                p_dict['joined_tournament'] = False
                p_dict['checked_in'] = False
            response.append(p_dict)
        return response
    else:
        results = await session.exec(stmt)
        return [p.dict() for p in results.all()]

@router.patch("/{player_id}", response_model=Player)
async def update_player(
    player_id: UUID,
    update_data: PlayerUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin only: Update player details.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    service = PlayerService(session)
    
    # Check if QQ already exists if being updated
    if update_data.qq_id:
        existing = await service.get_player_by_qq(update_data.qq_id)
        if existing and existing.id != player_id:
             raise HTTPException(status_code=400, detail="QQ ID already in use")

    updated_player = await service.update_player(
        player_id, 
        update_data.dict(exclude_unset=True)
    )
    
    if not updated_player:
        raise HTTPException(status_code=404, detail="Player not found")
        
    return updated_player

@router.delete("/{player_id}", status_code=204)
async def delete_player(
    player_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Admin only: Delete player.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    service = PlayerService(session)
    success = await service.delete_player(player_id)
    if not success:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return None
