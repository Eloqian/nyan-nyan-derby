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

        # 2. Create Stage (Audition)
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
        print(f"Created Stage: {stage.id}")

        # 3. Create Players
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
        print(f"Stage ID: {stage.id}")
        print("Use this ID in the Frontend '/ceremony' page.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed_data())
