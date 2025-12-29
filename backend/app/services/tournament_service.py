from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import Tournament, Stage, Group, Match, MatchParticipant, Player, Race, RaceResult
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
