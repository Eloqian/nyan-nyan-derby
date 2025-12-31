import pytest
from uuid import uuid4
from app.models.tournament import Stage, StageType
from app.services.logic.progression import ProgressionEngine

def test_determine_qualifiers_audition_6_into_4():
    """
    Test the rule: Top 4 from each group advance.
    """
    stage = Stage(
        name="Audition",
        stage_type=StageType.ROUND_ROBIN,
        sequence_order=1,
        # We can encode the rule in config, or hardcode it in engine based on stage name/order?
        # Ideally config: "top_n": 4
        rules_config={"advancement": {"type": "top_n", "value": 4}}
    )
    
    # 6 Players, ranked 1 to 6
    group_standings = [
        {"player_id": str(uuid4()), "rank": 1},
        {"player_id": str(uuid4()), "rank": 2},
        {"player_id": str(uuid4()), "rank": 3},
        {"player_id": str(uuid4()), "rank": 4},
        {"player_id": str(uuid4()), "rank": 5},
        {"player_id": str(uuid4()), "rank": 6},
    ]
    
    qualifiers = ProgressionEngine.determine_group_qualifiers(stage, group_standings)
    
    assert len(qualifiers) == 4
    # Ensure top 4 are in
    ids = [q["player_id"] for q in qualifiers]
    assert group_standings[0]["player_id"] in ids
    assert group_standings[3]["player_id"] in ids
    assert group_standings[4]["player_id"] not in ids

def test_determine_qualifiers_group_stage_split():
    """
    Test the rule: 
    1st -> Winner Bracket
    2nd -> Loser Bracket
    3rd -> Loser Bracket (implied 6->3)
    """
    stage = Stage(
        name="Group Stage Round 2",
        stage_type=StageType.ROUND_ROBIN,
        sequence_order=3,
        rules_config={
            "advancement": {
                "type": "position_map",
                "map": {
                    "1": "winner_bracket",
                    "2": "loser_bracket",
                    "3": "loser_bracket"
                }
            }
        }
    )
    
    group_standings = [
        {"player_id": "p1", "rank": 1},
        {"player_id": "p2", "rank": 2},
        {"player_id": "p3", "rank": 3},
        {"player_id": "p4", "rank": 4},
    ]
    
    qualifiers = ProgressionEngine.determine_group_qualifiers(stage, group_standings)
    
    # Should return list of dicts with 'destination'
    assert len(qualifiers) == 3
    
    p1 = next(q for q in qualifiers if q["player_id"] == "p1")
    assert p1["destination"] == "winner_bracket"
    
    p2 = next(q for q in qualifiers if q["player_id"] == "p2")
    assert p2["destination"] == "loser_bracket"

