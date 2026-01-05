from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import Player, User
from app.models.tournament import TournamentParticipant
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import csv
from io import StringIO

class PlayerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_player(self, player_id: UUID) -> Optional[Player]:
        return await self.session.get(Player, player_id)

    async def get_player_by_qq(self, qq_id: str) -> Optional[Player]:
        statement = select(Player).where(Player.qq_id == qq_id)
        result = await self.session.exec(statement)
        return result.first()

    async def create_player(self, in_game_name: str, qq_id: str, tournament_id: Optional[UUID] = None) -> Player:
        player = Player(in_game_name=in_game_name, qq_id=qq_id)
        
        # Auto-link if user already exists
        user_stmt = select(User).where(User.username == qq_id)
        user_res = await self.session.exec(user_stmt)
        user = user_res.first()
        if user:
            player.user_id = user.id

        self.session.add(player)
        # Flush to get ID
        await self.session.flush()
        
        if tournament_id:
            await self._add_to_tournament(player.id, tournament_id)
            
        await self.session.commit()
        await self.session.refresh(player)
        return player

    async def update_player(self, player_id: UUID, update_data: Dict[str, Any]) -> Optional[Player]:
        player = await self.get_player(player_id)
        if not player:
            return None
            
        for key, value in update_data.items():
            setattr(player, key, value)
            
        self.session.add(player)
        await self.session.commit()
        await self.session.refresh(player)
        return player

    async def delete_player(self, player_id: UUID) -> bool:
        player = await self.get_player(player_id)
        if not player:
            return False
            
        await self.session.delete(player)
        await self.session.commit()
        return True

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

    async def batch_create_players(self, players_data: List[dict], tournament_id: Optional[UUID] = None) -> int:
        """
        Bulk create players from a clean list.
        If tournament_id is provided, adds them to the tournament (even if they already existed).
        """
        count = 0
        processed_qqs = set()
        
        for p_data in players_data:
            qq_id = p_data.get('qq_id')
            if not qq_id:
                continue
                
            if qq_id in processed_qqs:
                continue
            
            existing = await self.get_player_by_qq(qq_id)
            
            if not existing:
                # Case 1: New Player
                player = Player(
                    in_game_name=p_data['in_game_name'],
                    qq_id=qq_id
                )
                
                # Auto-link if user already exists
                user_stmt = select(User).where(User.username == qq_id)
                user_res = await self.session.exec(user_stmt)
                user = user_res.first()
                if user:
                    player.user_id = user.id
                
                self.session.add(player)
                await self.session.flush() # Get ID
                count += 1
                
                # Directly add to tournament without query (since player is new)
                if tournament_id:
                    tp = TournamentParticipant(
                        tournament_id=tournament_id,
                        player_id=player.id,
                        checked_in=False,
                        checked_in_at=None
                    )
                    self.session.add(tp)
            else:
                # Case 2: Existing Player
                # Update name if changed? For now, keep existing.
                
                # Check if we should link user now (if it wasn't linked before)
                if existing.user_id is None:
                     user_stmt = select(User).where(User.username == qq_id)
                     user_res = await self.session.exec(user_stmt)
                     user = user_res.first()
                     if user:
                         existing.user_id = user.id
                         self.session.add(existing)

                if tournament_id:
                    await self._add_to_tournament(existing.id, tournament_id)
            
            processed_qqs.add(qq_id)
                
        await self.session.commit()
        return count

    async def _add_to_tournament(self, player_id: UUID, tournament_id: UUID):
        """Helper to safely add player to tournament if not already present."""
        stmt = select(TournamentParticipant).where(
            TournamentParticipant.player_id == player_id,
            TournamentParticipant.tournament_id == tournament_id
        )
        res = await self.session.exec(stmt)
        if not res.first():
            tp = TournamentParticipant(
                tournament_id=tournament_id,
                player_id=player_id,
                checked_in=False,
                checked_in_at=None
            )
            self.session.add(tp)

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
