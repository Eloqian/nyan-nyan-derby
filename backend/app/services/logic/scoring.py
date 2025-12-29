from typing import List, Dict, Any
from app.models import Player, RaceResult

class ScoringEngine:
    @staticmethod
    def calculate_race_points(results: List[RaceResult], players_map: Dict[str, Player]) -> List[RaceResult]:
        """
        Applies NPC Rank Shift and Assigns Points.
        results: list of RaceResult objects (with rank set).
        players_map: dict of player_id -> Player object (to check is_npc).
        """
        # 1. Sort by raw rank
        sorted_results = sorted(results, key=lambda r: r.rank)

        # 2. Filter out NPCs for ranking purposes
        valid_rank = 1
        points_map = {1: 9, 2: 5, 3: 3, 4: 2, 5: 1} # Default map, can be configurable later

        # We need to process them in order.
        # If a player is NPC, they get 0 points, but they consume a 'rank' slot in the raw race?
        # NO, the rule says: "NPCs do not get points and are not ranked... NPC is ignored... Player promoted"
        # So we iterate through the results. If it's a real player, they get the next available 'valid_rank'.

        for res in sorted_results:
            player = players_map.get(str(res.player_id))
            if not player or player.is_npc:
                # NPC gets 0 points, effectively ignored for ranking
                res.points_awarded = 0
                # Does their rank field change? Usually keep raw rank for history, but points reflect the shift.
                # But wait, if I am 2nd behind an NPC, I become 1st.
                # So my 'effective rank' is 1.
                continue

            # Real Player
            # Assign points based on current valid_rank
            res.points_awarded = points_map.get(valid_rank, 0)
            valid_rank += 1

        return sorted_results

    @staticmethod
    def calculate_match_score(match_participants, race_results):
        # This might be just an aggregation function
        pass
