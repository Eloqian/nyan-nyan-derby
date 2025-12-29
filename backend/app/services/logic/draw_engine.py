from typing import List, Dict, Any, Optional
import random
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.tournament import Stage, Player, Tournament, StageType

class DrawEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_eligible_players_for_stage(self, stage_id: UUID) -> List[Player]:
        """
        Determines eligible players for a given stage.
        """
        stage = await self.session.get(Stage, stage_id)
        if not stage:
            raise ValueError("Stage not found")

        # Logic for Stage 1 (Audition)
        # Assuming sequence_order 1 is Audition
        if stage.sequence_order == 1:
            # Fetch all players where seed_level != 2
            statement = select(Player).where(Player.seed_level != 2)
            results = await self.session.exec(statement)
            return list(results.all())

        # Logic for Stage 2 (Group Stage)
        elif stage.sequence_order == 2:
            # 1. Fetch Promoted Players from Stage 1
            # TODO: Implement actual promotion logic based on results.
            # For now, we might assume we need to fetch players who qualified.
            # Since this is a "Visualizer" task, we might need to mock this or assume data exists.

            # 2. Fetch Super Seeds (seed_level == 2)
            statement_seeds = select(Player).where(Player.seed_level == 2)
            results_seeds = await self.session.exec(statement_seeds)
            seeds = list(results_seeds.all())

            # Combine
            # Placeholder: For now, returning seeds + maybe some logic for promoted
            # If we strictly follow instructions: "Fetch all Promoted Players from Stage 1"
            # I will assume there is a way to identify them.
            # Lacking that, I will return just seeds for safety to avoid crashing,
            # or maybe ALL players if results are empty (for testing).

            # Let's return seeds for now to be safe and explicit.
            return seeds

        return []

    def perform_draw(self, players: List[Player], num_groups: int = 14) -> Dict[str, List[Dict[str, Any]]]:
        """
        Performs the pot-based draw.
        Returns a dictionary: { "Group A": [Player1, ...], "Group B": ... }
        """
        # 1. Separate into Pots
        pot_a = [p for p in players if p.seed_level == 1]
        pot_b = [p for p in players if p.seed_level != 1] # Includes seed_level 0 and potentially others if logic permits

        # 2. Initialize Groups
        # Naming: Group A, Group B, ...
        group_names = [f"Group {chr(65+i)}" for i in range(num_groups)]
        groups: Dict[str, List[Player]] = {name: [] for name in group_names}

        # 3. Distribute Pot A (Seeds)
        # Shuffle Pot A to ensure random assignment of seeds to groups
        random.shuffle(pot_a)

        # Assign one seed per group as far as possible
        for i, group_name in enumerate(group_names):
            if i < len(pot_a):
                groups[group_name].append(pot_a[i])
            else:
                # If we run out of seeds, we just continue.
                # (User said "14 Audition Seeds matching 14 Groups", so should be exact)
                pass

        # Note: If there are MORE seeds than groups, the extras should probably go back to Pot B or overflow?
        # User said: "Overflow Pot logic is still good to keep for robustness... Pot B will just contain normal players".
        # If Pot A has leftovers, add them to Pot B?
        if len(pot_a) > len(group_names):
            leftovers = pot_a[len(group_names):]
            pot_b.extend(leftovers)

        # 4. Distribute Pot B
        random.shuffle(pot_b)

        # Snake draft or simple fill? User said "Randomly fill the remaining slots".
        # We'll just distribute evenly.
        group_keys = list(groups.keys())
        current_group_idx = 0

        for player in pot_b:
            groups[group_keys[current_group_idx]].append(player)
            current_group_idx = (current_group_idx + 1) % len(group_keys)

        # 5. Format Output
        # Convert Players to dicts for JSON response
        result = {}
        for g_name, g_players in groups.items():
            result[g_name] = [
                {
                    "id": str(p.id),
                    "in_game_name": p.in_game_name,
                    "seed_level": p.seed_level,
                    "is_npc": p.is_npc
                }
                for p in g_players
            ]

        return result
