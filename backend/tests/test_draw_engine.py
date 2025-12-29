import pytest
import pytest_asyncio
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.tournament import Stage, StageType, Tournament
from app.models.user import Player
from app.services.logic.draw_engine import DrawEngine

# Use SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(name="session")
async def session_fixture():
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.mark.asyncio
async def test_draw_engine_logic(session: AsyncSession):
    # 1. Setup Data
    # Create Tournament and Stage
    tournament = Tournament(name="Test Tournament")
    session.add(tournament)
    await session.commit()
    await session.refresh(tournament)

    stage = Stage(
        tournament_id=tournament.id,
        name="Audition",
        stage_type=StageType.ROUND_ROBIN,
        sequence_order=1,
        rules_config={"group_count": 14}
    )
    session.add(stage)
    await session.commit()
    await session.refresh(stage)

    # Create 14 Seeds
    seeds = []
    for i in range(14):
        p = Player(in_game_name=f"Seed_{i}", qq_id=f"s_{i}", seed_level=1)
        session.add(p)
        seeds.append(p)

    # Create 20 Non-Seeds
    others = []
    for i in range(20):
        p = Player(in_game_name=f"Norm_{i}", qq_id=f"n_{i}", seed_level=0)
        session.add(p)
        others.append(p)

    await session.commit()

    # 2. Test get_eligible_players_for_stage
    engine = DrawEngine(session)
    players = await engine.get_eligible_players_for_stage(stage.id)

    # Expect 14 seeds + 20 others = 34 players
    assert len(players) == 34

    # 3. Test perform_draw
    groups_preview = engine.perform_draw(players, num_groups=14)

    # Check number of groups
    assert len(groups_preview) == 14
    assert "Group A" in groups_preview
    assert "Group N" in groups_preview

    # Check Seed Distribution (Pot A)
    # Each group should have exactly 1 seed
    # (Since we have 14 seeds and 14 groups)

    for g_name, g_players in groups_preview.items():
        # Check if first player is seed
        assert len(g_players) >= 1
        first_player = g_players[0]
        assert first_player['seed_level'] == 1

        # Count seeds in group
        seeds_in_group = sum(1 for p in g_players if p['seed_level'] == 1)
        assert seeds_in_group == 1

    # Check randomness?
    # Hard to test deterministically, but we can verify all players are present.
    all_drawn_ids = [p['id'] for g in groups_preview.values() for p in g]
    assert len(all_drawn_ids) == 34
    assert len(set(all_drawn_ids)) == 34 # No duplicates
