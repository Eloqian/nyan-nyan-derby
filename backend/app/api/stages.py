from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.models.tournament import Stage, Group, Match, GroupParticipant, Tournament, MatchParticipant, Race, RaceResult
from app.models.user import Player
from app.services.logic.draw_engine import DrawEngine
from uuid import UUID
from typing import Dict, List, Any, Optional
from sqlmodel import select
from pydantic import BaseModel

router = APIRouter()

# --- DTOs for View ---
class PlayerView(BaseModel):
    id: UUID
    name: str
    is_npc: bool

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

# ---------------------

@router.get("/{stage_id}/matches_view", response_model=List[GroupView])
async def get_stage_matches_view(
    stage_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Returns a hierarchical view of groups -> matches -> participants for the Referee Dashboard.
    """
    # 1. Get Groups
    stmt = select(Group).where(Group.stage_id == stage_id).order_by(Group.name)
    groups = (await session.exec(stmt)).all()

    view_data = []

    for group in groups:
        # Get Matches for Group
        m_stmt = select(Match).where(Match.group_id == group.id).order_by(Match.name) # simplified sort
        matches = (await session.exec(m_stmt)).all()

        matches_view = []
        for match in matches:
            # Get Participants
            mp_stmt = select(MatchParticipant, Player).join(Player).where(MatchParticipant.match_id == match.id)
            mp_results = (await session.exec(mp_stmt)).all()

            participants_view = []
            for mp, player in mp_results:
                participants_view.append(ParticipantView(
                    player=PlayerView(id=player.id, name=player.name, is_npc=player.is_npc)
                ))

            # Get Results (Assuming single race per match for now, or just aggregating)
            # We want to know if results exist to highlight the card
            # And maybe show current state (rank)
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

        view_data.append(GroupView(
            id=group.id,
            name=group.name,
            matches=matches_view
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

    return {"message": "Groups saved successfully", "count": len(saved_groups)}
