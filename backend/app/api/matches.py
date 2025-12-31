from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import select, col
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.services.tournament_service import TournamentService
from app.models.tournament import Match, MatchParticipant, Group, Stage, MatchStatus
from app.models.user import User
from app.api.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

router = APIRouter()

class PlayerRank(BaseModel):
    player_id: UUID
    rank: int

class RaceResultInput(BaseModel):
    race_number: int
    rankings: List[PlayerRank] # Explicit rank mapping

class MatchResponse(BaseModel):
    id: UUID
    name: str
    status: MatchStatus
    room_number: Optional[str]
    stage_name: str
    group_name: str
    host_player_id: Optional[UUID]
    is_host: bool = False
    opponent_names: List[str] = []

@router.get("/my", response_model=List[MatchResponse])
async def get_my_matches(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get active matches for the current user.
    """
    # 1. Find player ID for this user
    # Assuming 1-to-1 mapping for simplicity or taking the first one
    if not current_user.players:
        # Load players if not loaded (relationship) or query directly
        # For strictness, let's query
        pass 
    
    # We need to join MatchParticipant -> Player -> User
    # Or simplified: MatchParticipant where player_id in (user.players)
    
    # Let's get the player IDs first
    from app.models.user import Player
    stmt_players = select(Player.id).where(Player.user_id == current_user.id)
    player_ids = (await session.exec(stmt_players)).all()
    
    if not player_ids:
        return []

    # 2. Find Matches
    # Join MatchParticipant -> Match -> Group -> Stage
    stmt = (
        select(Match, Group.name, Stage.name)
        .join(MatchParticipant, Match.id == MatchParticipant.match_id)
        .join(Group, Match.group_id == Group.id)
        .join(Stage, Group.stage_id == Stage.id)
        .where(MatchParticipant.player_id.in_(player_ids)) # type: ignore
        .where(Match.status != MatchStatus.FINISHED) # Only active/pending
        .order_by(Match.start_time) # type: ignore
    )
    
    results = await session.exec(stmt)
    matches_data = results.all() # List of (Match, group_name, stage_name)
    
    response = []
    for match, group_name, stage_name in matches_data:
        # Check if user is host
        is_host = match.host_player_id in player_ids
        
        # Get opponents (names)
        # Separate query or pre-load? Separate is safer for now.
        opp_stmt = (
            select(Player.in_game_name)
            .join(MatchParticipant, Player.id == MatchParticipant.player_id)
            .where(MatchParticipant.match_id == match.id)
        )
        opp_names = (await session.exec(opp_stmt)).all()
        
        response.append(MatchResponse(
            id=match.id,
            name=match.name or f"{group_name} Match",
            status=match.status,
            room_number=match.room_number,
            stage_name=stage_name,
            group_name=group_name,
            host_player_id=match.host_player_id,
            is_host=is_host,
            opponent_names=list(opp_names)
        ))
        
    return response

@router.patch("/{match_id}/room")
async def update_room_number(
    match_id: UUID,
    room_number: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update room number. Any authenticated user can update it to help coordination.
    """
    match = await session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    # Permission check relaxed: Any logged-in user can update room number
    # This facilitates community help.
    
    match.room_number = room_number
    session.add(match)
    await session.commit()
    return {"message": "Room number updated", "room_number": room_number}

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
