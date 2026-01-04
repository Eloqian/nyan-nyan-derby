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

    async def create_player(self, in_game_name: str, qq_id: str) -> Player:
        player = Player(in_game_name=in_game_name, qq_id=qq_id)
        self.session.add(player)
        await self.session.commit()
        await self.session.refresh(player)
        return player

    async def validate_roster_csv(self, csv_content: str):
        """
        Parses CSV and checks for duplicates.
        Returns:
            {
                "valid": [{"in_game_name": "...", "qq_id": "..."}],
                "conflicts": { "qq_id": [{"in_game_name": "...", "row_num": 1}, ...] },
                "existing": ["qq_id", ...]
            }
        """
        reader = csv.DictReader(StringIO(csv_content))
        
        valid_records = []
        conflicts = {} # qq_id -> list of records
        seen_qqs = {} # qq_id -> first_record
        
        # 1. First pass: Identify file-internal duplicates
        rows = list(reader)
        for idx, row in enumerate(rows):
            if 'qq_id' not in row or 'in_game_name' not in row:
                continue
            
            qq_id = row['qq_id'].strip()
            name = row['in_game_name'].strip()
            
            if not qq_id:
                continue

            record = {"in_game_name": name, "qq_id": qq_id, "row": idx + 2} # CSV row numbers usually start at 1, +1 for header

            if qq_id in seen_qqs:
                # Found a duplicate!
                if qq_id not in conflicts:
                    # Move the original one to conflicts too
                    conflicts[qq_id] = [seen_qqs[qq_id]]
                conflicts[qq_id].append(record)
            else:
                seen_qqs[qq_id] = record

        # 2. Check against DB for the non-conflicting ones
        existing_qqs = []
        
        # Only process QQs that didn't have internal conflicts (conflicts must be resolved by user first)
        clean_candidates = [r for r in seen_qqs.values() if r['qq_id'] not in conflicts]
        
        for record in clean_candidates:
            existing = await self.get_player_by_qq(record['qq_id'])
            if existing:
                existing_qqs.append(record['qq_id'])
            else:
                valid_records.append({"in_game_name": record["in_game_name"], "qq_id": record["qq_id"]})

        return {
            "valid": valid_records,
            "conflicts": conflicts,
            "existing": existing_qqs
        }

    async def batch_create_players(self, players_data: List[dict]) -> int:
        """
        Bulk create players from a clean list.
        """
        count = 0
        processed_qqs = set()
        
        for p_data in players_data:
            qq_id = p_data.get('qq_id')
            if not qq_id:
                continue
                
            # 1. Check if we already processed this QQ in this batch
            if qq_id in processed_qqs:
                continue
            
            # 2. Check if it exists in DB
            existing = await self.get_player_by_qq(qq_id)
            if not existing:
                player = Player(
                    in_game_name=p_data['in_game_name'],
                    qq_id=qq_id
                )
                self.session.add(player)
                processed_qqs.add(qq_id)
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
