from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import Player, User
from typing import List, Optional
import csv
from io import StringIO

class PlayerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_player_by_qq(self, qq_id: str) -> Optional[Player]:
        statement = select(Player).where(Player.qq_id == qq_id)
        result = await self.session.exec(statement)
        return result.first()

    async def create_player(self, in_game_name: str, qq_id: str, is_npc: bool = False) -> Player:
        player = Player(in_game_name=in_game_name, qq_id=qq_id, is_npc=is_npc)
        self.session.add(player)
        await self.session.commit()
        await self.session.refresh(player)
        return player

    async def import_roster_from_csv(self, csv_content: str):
        """
        Expects CSV format: in_game_name,qq_id,is_npc
        """
        reader = csv.DictReader(StringIO(csv_content))
        count = 0
        for row in reader:
            qq_id = row['qq_id'].strip()
            existing = await self.get_player_by_qq(qq_id)
            if not existing:
                is_npc = row.get('is_npc', 'false').lower() == 'true'
                player = Player(
                    in_game_name=row['in_game_name'],
                    qq_id=qq_id,
                    is_npc=is_npc
                )
                self.session.add(player)
                count += 1
        await self.session.commit()
        return count

    async def claim_player(self, user: User, qq_id: str) -> bool:
        player = await self.get_player_by_qq(qq_id)
        if not player:
            return False # Player not found in roster

        if player.user_id:
            return False # Already claimed

        player.user_id = user.id
        self.session.add(player)
        await self.session.commit()
        return True
