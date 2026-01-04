import asyncio
import sys
import os
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app.db import engine
from app.models.tournament import Tournament, Stage, StageType
from app.models.user import Player, User

async def seed_data():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 1. Create Tournament
        tournament = Tournament(name="Meow Cup 2024")
        session.add(tournament)
        await session.commit()
        await session.refresh(tournament)
        print(f"Created Tournament: {tournament.id}")

        # 2. Create Stage 1 (Audition)
        stage1 = Stage(
            tournament_id=tournament.id,
            name="Audition",
            stage_type=StageType.ROUND_ROBIN,
            sequence_order=1,
            rules_config={
                "group_count": 14,
                "advancement": {"type": "top_n", "value": 4} # 6 into 4
            }
        )
        session.add(stage1)
        await session.commit()
        await session.refresh(stage1)
        print(f"Created Stage 1 (Audition): {stage1.id}")

        # 3. Create Stage 2 (Group Stage Round 1)
        stage2 = Stage(
            tournament_id=tournament.id,
            name="Group Stage Round 1",
            stage_type=StageType.ROUND_ROBIN,
            sequence_order=2,
            rules_config={
                "advancement": {"type": "top_n", "value": 4} # 6 into 4
            }
        )
        session.add(stage2)
        await session.commit()
        print(f"Created Stage 2 (Group Stage R1): {stage2.id}")

        # 4. Create Stage 3 (Group Stage Round 2)
        stage3 = Stage(
            tournament_id=tournament.id,
            name="Group Stage Round 2",
            stage_type=StageType.ROUND_ROBIN,
            sequence_order=3,
            rules_config={
                "advancement": {
                    "type": "position_map",
                    "map": {
                        "1": "winner_bracket",
                        "2": "loser_bracket",
                        "3": "loser_bracket"
                    }
                }
            }
        )
        session.add(stage3)
        await session.commit()
        print(f"Created Stage 3 (Group Stage R2): {stage3.id}")

        # 5. Create Players
        # Need 14 Seeds (seed_level=1)
        # Need ~82 Non-seeds (seed_level=0)

        # Seeds
        for i in range(14):
            player = Player(
                in_game_name=f"SeedPlayer_{i+1}",
                qq_id=f"seed_{i+1}",
                seed_level=1
            )
            session.add(player)

        # Non-Seeds
        for i in range(82):
            player = Player(
                in_game_name=f"Normie_{i+1}",
                qq_id=f"normie_{i+1}",
                seed_level=0
            )
            session.add(player)

        await session.commit()
        print("Created 96 Players (14 Seeds)")

        print("\n\n=== TEST INFO ===")
        print(f"Stage ID: {stage1.id}")
        print("Use this ID in the Frontend '/ceremony' page.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed_data())
