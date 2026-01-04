from typing import List, Dict, Any
from app.models import Player, RaceResult

class ScoringEngine:
    @staticmethod
    def calculate_race_points(results: List[RaceResult], players_map: Dict[str, Player]) -> List[RaceResult]:
        """
        Assigns Points based on rank.
        results: list of RaceResult objects (with rank set).
        players_map: dict of player_id -> Player object.
        """
        # 1. Sort by raw rank
        sorted_results = sorted(results, key=lambda r: r.rank)

        # 2. Assign points
        valid_rank = 1
        points_map = {1: 9, 2: 5, 3: 3, 4: 2, 5: 1} # Default map, can be configurable later

        for res in sorted_results:
            player = players_map.get(str(res.player_id))
            if not player:
                res.points_awarded = 0
                continue

            # Assign points based on current valid_rank
            res.points_awarded = points_map.get(valid_rank, 0)
            valid_rank += 1

        return sorted_results

    @staticmethod
    def calculate_match_score(race_results: List[RaceResult], match_config: Dict[str, Any] = {}) -> List[Dict[str, Any]]:
        """
        Aggregates race results to determine the match outcome.
        Returns a list of dicts:
        [
            {
                "player_id": uuid,
                "total_points": int,
                "wins": int,
                "is_ace": bool
            },
            ...
        ]
        """
        from collections import defaultdict

        player_stats = defaultdict(lambda: {"points": 0, "wins": 0})
        unique_races = set()

        for res in race_results:
            unique_races.add(res.race_id)
            pid = res.player_id
            player_stats[pid]["points"] += res.points_awarded
            # Assuming rank 1 is a win. Note: This is raw rank.
            # If we want "effective win" (after NPC removal), we should check points?
            # Usually "1st place" means highest points awarded in that race.
            # But let's stick to valid_rank logic. If I got 9 points (default for 1st), I won.
            # Or simpler: check if rank == 1? No, because of NPCs.
            # Let's rely on points. If points == max_points (9), it's a win?
            # Safer: count how many races.
            # Let's assume rank=1 is a win for now, subject to NPC logic which might have already adjusted it?
            # No, 'calculate_race_points' does not change 'rank', it sets 'points_awarded'.
            # A win is defined as getting the maximum points available in the race?
            # Let's count wins as "having the highest points in a race".
            pass

        # Re-iterate to count wins correctly per race
        # Group by race_id first
        races_map = defaultdict(list)
        for res in race_results:
            races_map[res.race_id].append(res)

        total_races = len(races_map)
        
        for race_id, results in races_map.items():
            # Find max points in this race
            if not results:
                continue
            max_pts = max(r.points_awarded for r in results)
            # If max_pts is 0 (e.g. all NPCs?), no one wins.
            if max_pts > 0:
                for r in results:
                    if r.points_awarded == max_pts:
                        player_stats[r.player_id]["wins"] += 1

        # Apply Ace Bonus
        ace_bonus = match_config.get("ace_bonus_points", 0)
        
        final_scores = []
        for pid, stats in player_stats.items():
            is_ace = False
            if total_races > 0 and stats["wins"] > (total_races / 2):
                stats["points"] += ace_bonus
                is_ace = True
            
            final_scores.append({
                "player_id": pid,
                "total_points": stats["points"],
                "wins": stats["wins"],
                "is_ace": is_ace
            })

        # Sort by total points descending
        final_scores.sort(key=lambda x: x["total_points"], reverse=True)
        return final_scores
