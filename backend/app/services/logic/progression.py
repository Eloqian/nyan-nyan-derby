from typing import List, Dict
from app.models import Match, Stage
import math

class ProgressionEngine:
    @staticmethod
    def calculate_dominance_bonus(stage: Stage, player_id: str, player_matches: List[Match], all_race_results: List[Any]) -> int:
        """
        Calculates Dominance Bonus based on Stage rules.
        Rule: If 1st_count > floor(total_rounds / 2), bonus = (count - floor) * 2
        """
        rules = stage.rules_config or {}
        bonus_rules = rules.get("bonus_rules", [])

        # Check if dominance bonus is enabled
        dominance_rule = next((r for r in bonus_rules if r["type"] == "dominance_bonus"), None)
        if not dominance_rule:
            return 0

        # 1. Count 1st places for this player in this stage
        # We need race results where effective rank (or points == 9) was 1st.
        # This implies we need to know the 'effective rank' from the scoring phase.
        # Assuming points_awarded == 9 means 1st place.

        first_place_count = 0
        for res in all_race_results:
            if str(res.player_id) == str(player_id) and res.points_awarded == 9:
                first_place_count += 1

        # 2. Determine Total Rounds
        # "Total Rounds" usually means number of matches played by the player?
        # Or total rounds in the stage definition?
        # The example said "In a 3-round stage (Total=3)...".
        # This usually implies the number of Matches the player participated in.
        total_rounds = len(player_matches)

        if total_rounds == 0:
            return 0

        threshold = math.floor(total_rounds / 2)

        if first_place_count > threshold:
            return (first_place_count - threshold) * 2

        return 0
