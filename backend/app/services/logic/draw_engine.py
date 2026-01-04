from typing import List, Dict, Any, Optional
import random
from uuid import UUID
from collections import defaultdict
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.tournament import Stage, Player, Tournament, StageType, Group, Match, Race, RaceResult
from app.services.logic.progression import ProgressionEngine
from app.services.logic.scoring import ScoringEngine

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

        # Logic for Stage 2 (Group Stage) and beyond
        # We generally look for the previous stage.
        else:
            prev_stage_order = stage.sequence_order - 1
            stmt_stage = select(Stage).where(
                Stage.tournament_id == stage.tournament_id,
                Stage.sequence_order == prev_stage_order
            )
            prev_stage = (await self.session.exec(stmt_stage)).first()
            
            promoted_players = []
            
            if prev_stage:
                # 1. Fetch Promoted Players from Stage 1 (or previous)
                promoted_ids = set()
                
                # Get all groups from previous stage
                stmt_groups = select(Group).where(Group.stage_id == prev_stage.id)
                groups = (await self.session.exec(stmt_groups)).all()
                
                for group in groups:
                    # Calculate standings for this group
                    # Fetch RaceResults for this group
                    stmt_results = (
                        select(RaceResult, Match)
                        .join(Race, RaceResult.race_id == Race.id)
                        .join(Match, Race.match_id == Match.id)
                        .where(Match.group_id == group.id)
                    )
                    results = (await self.session.exec(stmt_results)).all()
                    
                    # Aggregate Results
                    results_by_match = defaultdict(list)
                    for rr, match in results:
                        results_by_match[match.id].append(rr)
                        
                    group_stats = defaultdict(lambda: {"points": 0, "wins": 0, "player_id": None})
                    
                    for match_id, race_results in results_by_match.items():
                        # We use previous stage's rules for scoring
                        match_scores = ScoringEngine.calculate_match_score(race_results, prev_stage.rules_config)
                        for score in match_scores:
                            pid = str(score["player_id"])
                            group_stats[pid]["player_id"] = pid
                            group_stats[pid]["points"] += score["total_points"]
                            group_stats[pid]["wins"] += score["wins"]

                    # Convert to list and sort
                    standings = list(group_stats.values())
                    # Sort by Points desc, then Wins desc
                    standings.sort(key=lambda x: (x["points"], x["wins"]), reverse=True)
                    
                    # Add Rank
                    for i, entry in enumerate(standings):
                        entry["rank"] = i + 1
                    
                    # Determine Qualifiers using ProgressionEngine
                    # Passing prev_stage because the advancement rules are usually defined THERE 
                    # (e.g. "Top 4 from this stage advance")
                    # OR defined in current stage? Usually rules like "Top 4 advance" are property of the source stage.
                    # Let's assume prev_stage.rules_config has 'advancement'
                    qualifiers = ProgressionEngine.determine_group_qualifiers(prev_stage, standings)
                    
                    for q in qualifiers:
                        promoted_ids.add(q["player_id"])

                if promoted_ids:
                    stmt_promoted = select(Player).where(Player.id.in_(list(promoted_ids)))
                    promoted_players = list((await self.session.exec(stmt_promoted)).all())

            # 2. Fetch Super Seeds (seed_level == 2) if this is Stage 2
            # Specific rule: Stage 2 includes Super Seeds.
            seeds = []
            if stage.sequence_order == 2:
                statement_seeds = select(Player).where(Player.seed_level == 2)
                results_seeds = await self.session.exec(statement_seeds)
                seeds = list(results_seeds.all())

            # Combine unique players
            # Use a dict by ID to deduplicate if logic overlaps
            final_map = {str(p.id): p for p in promoted_players}
            for p in seeds:
                final_map[str(p.id)] = p
                
            return list(final_map.values())

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
                    "seed_level": p.seed_level
                }
                for p in g_players
            ]

        return result
