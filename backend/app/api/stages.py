from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db import get_session
from app.models.tournament import Stage, Group, Match, GroupParticipant, Tournament
from app.models.user import Player
from app.services.logic.draw_engine import DrawEngine
from uuid import UUID
from typing import Dict, List, Any
from sqlmodel import select

router = APIRouter()

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
