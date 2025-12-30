from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import Tournament, Stage, Group, Match, MatchParticipant, Player, Race, RaceResult, GroupParticipant
from app.services.logic.scoring import ScoringEngine
from typing import List, Dict
import random

class TournamentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tournament(self, name: str) -> Tournament:
        tourney = Tournament(name=name)
        self.session.add(tourney)
        await self.session.commit()
        await self.session.refresh(tourney)
        return tourney

    async def create_stage(self, tournament_id: str, name: str, stage_type: str, rules: Dict = {}) -> Stage:
        stage = Stage(
            tournament_id=tournament_id,
            name=name,
            stage_type=stage_type,
            sequence_order=1, # simplified
            rules_config=rules
        )
        self.session.add(stage)
        await self.session.commit()
        await self.session.refresh(stage)
        return stage

    async def generate_groups_randomly(self, stage_id: str, player_ids: List[str], group_size: int = 6):
        """
        Randomly assigns players to groups.
        """
        stage = await self.session.get(Stage, stage_id)
        if not stage:
            return None

        # Shuffle players
        shuffled = list(player_ids)
        random.shuffle(shuffled)

        # Chunk into groups
        chunks = [shuffled[i:i + group_size] for i in range(0, len(shuffled), group_size)]

        created_groups = []
        for i, chunk in enumerate(chunks):
            group = Group(stage_id=stage.id, name=f"Group {i+1}")
            self.session.add(group)
            await self.session.commit() # Commit to get ID
            await self.session.refresh(group)

            # Create Matches (Simplified: 1 match per group for now, or based on logic)
            # The rule says "Group Stage... 6 people... top 4 advance".
            # Usually they play one big match (9 horses)? Or multiple?
            # Rule: "Each person brings 3 horses, 3 people per group, 9 horses melee" -> Wait.
            # The rule says: "Group of 6 people."
            # "Each person brings 3 horses, 3 people per group..."
            # This implies a Group of 6 is split into 2 Matches of 3 people?
            # Or the 'Group' is just a logical container for 6 people, and they play X matches?
            # Re-reading Rule 4: "3 people per group, 9 horses mixed battle".
            # BUT Rule 3 says "Group of 6".
            # So likely: The 6 people in a "Group" play against each other in sub-matches.
            # Example: 6 people = A,B,C,D,E,F.
            # Maybe they play 2 matches: (A,B,C) and (D,E,F)? Or everyone plays everyone?
            # Given the text "Group of 6... Top 4 advance", and "3 people per match",
            # It's likely they play multiple rounds to determine the Top 4.
            # FOR NOW: I will just assign them to the Group. Match generation is a separate step.

            created_groups.append(group)

        return created_groups

    async def generate_matches_for_stage(self, stage_id: str) -> List[Match]:
        """
        Generates matches for all groups in the stage.
        Specific logic for "6-player group audition" (6人组海选).
        """
        stage = await self.session.get(Stage, stage_id)
        if not stage:
            raise ValueError("Stage not found")

        # Get all groups in the stage
        stmt = select(Group).where(Group.stage_id == stage_id)
        groups = (await self.session.exec(stmt)).all()

        created_matches = []
        for group in groups:
             matches = await self._generate_matches_for_group(group)
             created_matches.extend(matches)

        return created_matches

    async def _generate_matches_for_group(self, group: Group) -> List[Match]:
        """
        Logic for 6-player group:
        - 10 matches total
        - 3 players per match
        - Each player plays exactly 5 matches
        - Balanced pairs (BIBD)
        - Host assignment balanced
        """
        # Fetch participants
        stmt = select(GroupParticipant).where(GroupParticipant.group_id == group.id)
        participants = (await self.session.exec(stmt)).all()
        player_ids = [p.player_id for p in participants]

        # We expect 6 players. If not 6, we log warning/error or proceed best effort?
        # For this specific task, we implement the 6-player logic.
        if len(player_ids) != 6:
            # If not 6, we skip match generation for this group to avoid errors, or raise.
            # Assuming strictly 6 as per requirement.
            # But let's raise for visibility if this logic is strictly for 6.
            raise ValueError(f"Group {group.id} has {len(player_ids)} players, expected 6 for audition logic.")

        # Hardcoded matrix (0-5 indices)
        # 10 Matches, 3 Participants each.
        matches_indices = [
           (0, 1, 2), (0, 1, 3), (0, 2, 4), (0, 3, 5), (0, 4, 5),
           (1, 2, 5), (1, 3, 4), (1, 4, 5), (2, 3, 4), (2, 3, 5)
        ]

        matches = []

        # Host tracking: player_id -> count
        host_counts = {pid: 0 for pid in player_ids}

        for idx, indices in enumerate(matches_indices):
            # Resolve players for this match
            match_player_ids = [player_ids[i] for i in indices]

            # Determine Host
            # Sort match_players by host_count ascending, then random tie-break
            candidates = list(match_player_ids)
            random.shuffle(candidates)
            candidates.sort(key=lambda p: host_counts[p])

            host_id = candidates[0]
            host_counts[host_id] += 1

            # Create Match
            match = Match(
                group_id=group.id,
                name=f"{group.name} - Match {idx + 1}",
                host_player_id=host_id,
                status="pending"
            )
            self.session.add(match)
            await self.session.commit()
            await self.session.refresh(match)

            # Create Participants
            for pid in match_player_ids:
                mp = MatchParticipant(match_id=match.id, player_id=pid)
                self.session.add(mp)

            matches.append(match)

        await self.session.commit()
        return matches

    async def record_race_result(self, match_id: str, race_number: int, rankings: List[str]):
        """
        rankings: List of player_ids in order (1st to last).
        """
        # 1. Get Match & Participants
        match = await self.session.get(Match, match_id)
        participants = await self.session.exec(select(MatchParticipant).where(MatchParticipant.match_id == match_id))
        participant_players = [p.player_id for p in participants.all()]

        # Load full player objects to check is_npc
        players_stmt = select(Player).where(Player.id.in_(participant_players)) # type: ignore
        players_result = await self.session.exec(players_stmt)
        players_map = {str(p.id): p for p in players_result.all()}

        # 2. Create/Get Race
        # Check if race exists
        race_stmt = select(Race).where(Race.match_id == match_id, Race.race_number == race_number)
        race_res = await self.session.exec(race_stmt)
        race = race_res.first()
        if not race:
            race = Race(match_id=match_id, race_number=race_number)
            self.session.add(race)
            await self.session.commit()
            await self.session.refresh(race)

        # 3. Create RaceResults (Temporary objects)
        results = []
        for rank_idx, pid in enumerate(rankings):
            res = RaceResult(
                race_id=race.id,
                player_id=pid,
                rank=rank_idx + 1
            )
            results.append(res)

        # 4. Calculate Points (Engine)
        calculated_results = ScoringEngine.calculate_race_points(results, players_map)

        # 5. Save to DB
        for res in calculated_results:
            self.session.add(res)

        await self.session.commit()
        return calculated_results
