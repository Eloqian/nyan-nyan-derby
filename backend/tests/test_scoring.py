import pytest
import pytest_asyncio
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.tournament import Stage, Match, Group, Race, RaceResult
from app.models.user import Player
from app.services.logic.scoring import ScoringEngine
from app.services.tournament_service import TournamentService
from uuid import uuid4

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

def test_calculate_match_score_ace_bonus():
    # Setup
    pid_a = str(uuid4())
    pid_b = str(uuid4())
    rid_1 = str(uuid4())
    rid_2 = str(uuid4())

    # 2 Races. Player A wins both. (2/2 = 100% > 50%)
    r1_pA = RaceResult(player_id=pid_a, rank=1, points_awarded=9, race_id=rid_1) 
    r1_pB = RaceResult(player_id=pid_b, rank=2, points_awarded=5, race_id=rid_1)

    r2_pA = RaceResult(player_id=pid_a, rank=1, points_awarded=9, race_id=rid_2)
    r2_pB = RaceResult(player_id=pid_b, rank=2, points_awarded=5, race_id=rid_2)

    results = [r1_pA, r1_pB, r2_pA, r2_pB]
    config = {"ace_bonus_points": 7}

    # Execute
    scores = ScoringEngine.calculate_match_score(results, config)

    # Verify
    # A: 18 points + 7 bonus = 25. Wins: 2. Is Ace: True.
    score_A = next(s for s in scores if s["player_id"] == pid_a)
    assert score_A["total_points"] == 25
    assert score_A["wins"] == 2
    assert score_A["is_ace"] == True
    
    # B: 10 points. Wins: 0. Is Ace: False.
    score_B = next(s for s in scores if s["player_id"] == pid_b)
    assert score_B["total_points"] == 10
    assert score_B["wins"] == 0
    assert score_B["is_ace"] == False

@pytest.mark.asyncio
async def test_get_stage_standings(session: AsyncSession):
    # 1. Setup Data
    # Create Tournament and Stage
    # Use raw UUIDs for convenience or let DB generate
    from app.models.tournament import Tournament
    
    tourney = Tournament(name="Test Cup")
    session.add(tourney)
    await session.commit()
    await session.refresh(tourney)

    stage = Stage(
        tournament_id=tourney.id,
        name="Groups",
        stage_type="round_robin",
        sequence_order=1,
        rules_config={"ace_bonus_points": 2}
    )
    session.add(stage)
    await session.commit()
    await session.refresh(stage)

    # Create Players
    p1 = Player(in_game_name="Alice", qq_id="111")
    p2 = Player(in_game_name="Bob", qq_id="222")
    session.add(p1)
    session.add(p2)
    await session.commit()
    await session.refresh(p1)
    await session.refresh(p2)

    # Create Group & Match
    group = Group(stage_id=stage.id, name="Group A")
    session.add(group)
    await session.commit()
    await session.refresh(group)

    match = Match(group_id=group.id, name="M1")
    session.add(match)
    await session.commit()
    await session.refresh(match)

    # Create Race & Results
    # Alice wins race 1 (9 pts), Bob 2nd (5 pts)
    # Only 1 race, so Alice wins 1/1 > 50% -> Ace Bonus (+2)
    # Alice Total: 9 + 2 = 11. Bob: 5.
    
    race = Race(match_id=match.id, race_number=1)
    session.add(race)
    await session.commit()
    await session.refresh(race)

    rr1 = RaceResult(race_id=race.id, player_id=p1.id, rank=1, points_awarded=9)
    rr2 = RaceResult(race_id=race.id, player_id=p2.id, rank=2, points_awarded=5)
    session.add(rr1)
    session.add(rr2)
    await session.commit()

    # 2. Test Service
    service = TournamentService(session)
    standings = await service.get_stage_standings(str(stage.id))

    # Verify
    assert len(standings) == 2
    
    # Alice should be 1st
    alice = standings[0]
    assert alice["player_name"] == "Alice"
    assert alice["rank"] == 1
    assert alice["total_points"] == 11
    assert alice["wins"] == 1
    assert alice["matches_played"] == 1

    # Bob should be 2nd
    bob = standings[1]
    assert bob["player_name"] == "Bob"
    assert bob["rank"] == 2
    assert bob["total_points"] == 5
    assert bob["wins"] == 0
