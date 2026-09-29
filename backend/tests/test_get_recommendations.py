#Tests for get_recommendations 

from conftest import make_player, add_players
from recommend_player import (
    get_recommendations, REQUIRED_COUNTS, OVERVIEW_SUGGESTION_COUNT,
)

FULL_SQUAD = REQUIRED_COUNTS  # 2 GKP / 5 DEF / 5 MID / 3 FWD


def build_players(counts, start_id, cost=5.0):

    players = []
    next_id = start_id

    for position, count in counts.items():
        for _ in range(count):
            players.append(make_player(next_id, position, cost=cost, team_id=(next_id % 8) + 1))
            next_id += 1

    return players


# builds a squad as well as a pool of unowned players to recommned from
def setup_squad(session, squad_counts):

    squad = build_players(squad_counts, start_id=1)
   
    pool = build_players({"GKP": 4, "DEF": 4, "MID": 4, "FWD": 4}, start_id=100)

    add_players(session, squad + pool)

    # squad players score badly, pool players score well range of prices and clubs so restrictions do not block
    all_scores = {player.id: 10.0 for player in squad}
    all_scores.update({player.id: 80.0 for player in pool})

    return [player.id for player in squad], all_scores


def test_empty_squad_needs_filling_in_every_position(session):
    _, all_scores = setup_squad(session, {})

    recommendations = get_recommendations([], session, all_scores=all_scores)

    assert {position: info["action"] for position, info in recommendations.items()} == {
        "GKP": "fill", "DEF": "fill", "MID": "fill", "FWD": "fill",
    }


def test_full_squad_gets_upgrades_in_every_position(session):
    squad_ids, all_scores = setup_squad(session, FULL_SQUAD)

    recommendations = get_recommendations(squad_ids, session, all_scores=all_scores)

    assert all(info["action"] == "upgrade" for info in recommendations.values())


def test_part_built_squad_gets_both_kinds_of_advice_at_once(session):
    # everything complete except defence, which is 2 of 5
    squad_counts = {**FULL_SQUAD, "DEF": 2}
    squad_ids, all_scores = setup_squad(session, squad_counts)

    recommendations = get_recommendations(squad_ids, session, all_scores=all_scores)

    assert recommendations["DEF"]["action"] == "fill"
    assert recommendations["DEF"]["missing"] == 3
    assert recommendations["GKP"]["action"] == "upgrade"
    assert recommendations["MID"]["action"] == "upgrade"
    assert recommendations["FWD"]["action"] == "upgrade"


def test_over_filled_position_is_treated_as_full_not_short(session):
    # 6 defenders when 5 are allowed - "missing" floors at 0, so it takes the
    # upgrade path rather than asking for even more defenders
    squad_counts = {**FULL_SQUAD, "DEF": 6}
    squad_ids, all_scores = setup_squad(session, squad_counts)

    recommendations = get_recommendations(squad_ids, session, all_scores=all_scores)

    assert recommendations["DEF"]["action"] == "upgrade"
    assert recommendations["DEF"]["filled"] == 6
    assert recommendations["DEF"]["missing"] == 0


def test_upgrade_with_nothing_better_reports_no_replacement_and_no_score(session):

    squad_ids, all_scores = setup_squad(session, FULL_SQUAD)
    all_scores = {player_id: 99.0 if player_id in squad_ids else 10.0 for player_id in all_scores}

    recommendations = get_recommendations(squad_ids, session, all_scores=all_scores)

    for info in recommendations.values():
        assert info["suggested_replacement"] is None
        assert info["suggested_score"] is None


def test_fill_suggestions_are_capped_for_the_overview(session):

    _, all_scores = setup_squad(session, {})
    recommendations = get_recommendations([], session, all_scores=all_scores)

    for info in recommendations.values():
        assert len(info["suggestions"]) == OVERVIEW_SUGGESTION_COUNT
