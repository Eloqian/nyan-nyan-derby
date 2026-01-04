from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.models.tournament import Stage, Group, Match, GroupParticipant, Tournament, MatchParticipant, Race, RaceResult
from app.models.user import Player
from app.services.logic.draw_engine import DrawEngine
from app.services.tournament_service import TournamentService
from app.models.view_models import StageStandingsResponse, PlayerStanding
from uuid import UUID
from typing import Dict, List, Any, Optional
from sqlmodel import select
from pydantic import BaseModel

router = APIRouter()

# --- DTOs for View ---
class PlayerView(BaseModel):
    id: UUID
    name: str

class ParticipantView(BaseModel):
    player: PlayerView

class MatchView(BaseModel):
    id: UUID
    name: str | None
    status: str
    host_player_id: Optional[UUID]
    participants: List[ParticipantView]
    # Optionally include existing results if any
    results: List[Dict[str, Any]] = []

class GroupView(BaseModel):
    id: UUID
    name: str
    matches: List[MatchView]
    standings: List[Dict[str, Any]] = []

# ---------------------

@router.get("/", response_model=List[Stage])
async def list_stages(
    session: AsyncSession = Depends(get_session),
    tournament_id: Optional[UUID] = None
):
    """
    List all stages, optionally filtered by tournament_id.
    Ordered by sequence_order.
    """
    if tournament_id:
        stmt = select(Stage).where(Stage.tournament_id == tournament_id).order_by(Stage.sequence_order)
    else:
        stmt = select(Stage).order_by(Stage.sequence_order)
    result = await session.exec(stmt)
    return result.all()


@router.get("/{stage_id}/standings", response_model=StageStandingsResponse)
async def get_stage_standings(
    stage_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Returns the calculated standings (leaderboard) for the stage.
    """
    service = TournamentService(session)
    try:
        standings_data = await service.get_stage_standings(str(stage_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Convert to Pydantic models
    player_standings = [
        PlayerStanding(
            rank=s['rank'],
            player_id=s['player_id'],
            player_name=s['player_name'],
            total_points=s['total_points'],
            wins=s['wins'],
            matches_played=s['matches_played']
        )
        for s in standings_data
    ]

    return StageStandingsResponse(
        stage_id=stage_id,
        standings=player_standings
    )

@router.get("/{stage_id}/matches_view", response_model=List[GroupView])
async def get_stage_matches_view(
    stage_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Returns a hierarchical view of groups -> matches -> participants for the Referee Dashboard.
    """
    service = TournamentService(session)
    
    # 1. Get Groups
    stmt = select(Group).where(Group.stage_id == stage_id).order_by(Group.name)
    groups = (await session.exec(stmt)).all()
    
    # Pre-calculate standings for the whole stage to distribute to groups
    # This is a bit inefficient (re-fetching), but simpler to implement reuse
    # Or we can filter standings by group.
    full_standings = await service.get_stage_standings(str(stage_id))
    # Map standings by Player ID for easy group lookup? 
    # Actually we want standings PER GROUP usually for Group Stage?
    # The current `get_stage_standings` aggregates by stage. 
    # If the stage is "Group Stage", we usually want rankings within the group.
    # But `get_stage_standings` returns a flat list. 
    # Let's filter it by group participants.

    view_data = []

    for group in groups:
        # Get Matches for Group
        m_stmt = select(Match).where(Match.group_id == group.id).order_by(Match.name) # simplified sort
        matches = (await session.exec(m_stmt)).all()

        matches_view = []
        group_player_ids = set()

        for match in matches:
            # Get Participants
            mp_stmt = select(MatchParticipant, Player).join(Player).where(MatchParticipant.match_id == match.id)
            mp_results = (await session.exec(mp_stmt)).all()

            participants_view = []
            for mp, player in mp_results:
                group_player_ids.add(str(player.id))
                participants_view.append(ParticipantView(
                    player=PlayerView(id=player.id, name=player.in_game_name)
                ))

            # Get Results
            r_stmt = select(RaceResult).join(Race).where(Race.match_id == match.id)
            race_results = (await session.exec(r_stmt)).all()

            results_list = []
            for rr in race_results:
                results_list.append({
                    "player_id": str(rr.player_id),
                    "rank": rr.rank,
                    "points": rr.points_awarded
                })

            matches_view.append(MatchView(
                id=match.id,
                name=match.name,
                status=match.status,
                host_player_id=match.host_player_id,
                participants=participants_view,
                results=results_list
            ))
            
        # Filter standings for this group
        group_standings = [s for s in full_standings if str(s['player_id']) in group_player_ids]
        # Re-rank within group
        group_standings.sort(key=lambda x: (x["total_points"], x["wins"]), reverse=True)
        for i, s in enumerate(group_standings):
            s['rank'] = i + 1

        view_data.append(GroupView(
            id=group.id,
            name=group.name,
            matches=matches_view,
            standings=group_standings
        ))

    return view_data

@router.post("/{stage_id}/draw_preview")
async def draw_preview(
    stage_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Generates a preview of the group draw for the given stage.
    Does NOT save to DB.
    """
    engine = DrawEngine(session)
    try:
        players = await engine.get_eligible_players_for_stage(stage_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not players:
        raise HTTPException(status_code=400, detail="No eligible players found for this stage.")

    # Determine num_groups
    # Try to get from stage rules, else default to 14 (as per requirement)
    stage = await session.get(Stage, stage_id)
    rules = stage.rules_config or {}
    num_groups = rules.get("group_count", 14)

    # Perform Draw
    groups_preview = engine.perform_draw(players, num_groups=num_groups)

    return groups_preview


@router.post("/{stage_id}/groups")
async def save_groups(
    stage_id: UUID,
    groups_data: Dict[str, List[Dict[str, Any]]],
    session: AsyncSession = Depends(get_session)
):
    """
    Saves the group structure to the database.
    Input: { "Group A": [ { "id": "...", ... }, ... ], ... }
    """
    # ... (existing code) ...
    stage = await session.get(Stage, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")

    # Clear existing groups for this stage logic might be needed here,
    # but for now we append/create.

    saved_groups = []

    for group_name, players_list in groups_data.items():
        # Create Group
        group = Group(stage_id=stage_id, name=group_name)
        session.add(group)
        await session.commit()
        await session.refresh(group)
        saved_groups.append(group)

        # Add Participants
        for player_data in players_list:
            player_id = UUID(player_data['id'])
            # Create Link
            # Verify player exists? Ideally yes, but assuming trusted input for now or FK constraint will fail.
            participant = GroupParticipant(group_id=group.id, player_id=player_id)
            session.add(participant)

        await session.commit()
    
    # After saving groups, generate matches automatically?
    # Usually yes, but user might want to review. 
    # For streamlined flow: YES.
    # Generate Matches
    service = TournamentService(session)
    await service.generate_matches_for_stage(str(stage_id))

    return {"message": "Groups saved and matches generated", "count": len(saved_groups)}

@router.post("/{stage_id}/settle")
async def settle_stage(
    stage_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Mark current stage as complete and find the next stage for the draw.
    Returns: { "next_stage_id": "...", "next_stage_name": "..." }
    """
    stage = await session.get(Stage, stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
        
    # 1. Check if all matches are finished?
    # For flexibility, we allow force settle. (Admin knows best)
    
    # 2. Find next stage
    stmt = select(Stage).where(
        Stage.tournament_id == stage.tournament_id,
        Stage.sequence_order == stage.sequence_order + 1
    )
    next_stage = (await session.exec(stmt)).first()
    
    if not next_stage:
        return {"message": "Tournament Completed! No next stage.", "next_stage_id": None}
        
    return {
        "message": f"Ready for {next_stage.name}",
        "next_stage_id": str(next_stage.id),
        "next_stage_name": next_stage.name
    }
