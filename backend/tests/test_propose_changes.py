# tests the checks in tools/propose_changes.py - the code that decides whether
# the transfers the AI suggests are allowed before the user can apply them

from conftest import make_player, add_players
from tools.propose_changes import call_propose_changes

# ids of the test squad built below, by position
GOALKEEPERS = [1, 2]
DEFENDERS = [3, 4, 5, 6, 7]
MIDFIELDERS = [8, 9, 10, 11, 12]
FORWARDS = [13, 14, 15]


def build_squad(cost):
    # a full, legal 15. Clubs are spread with (id % 8) + 1, so no club has more
    # than 2 players - leaves room for the club-limit test to push one to 4
    squad = []

    for player_id in GOALKEEPERS:
        squad.append(make_player(player_id, "GKP", cost=cost, team_id=(player_id % 8) + 1))
    for player_id in DEFENDERS:
        squad.append(make_player(player_id, "DEF", cost=cost, team_id=(player_id % 8) + 1))
    for player_id in MIDFIELDERS:
        squad.append(make_player(player_id, "MID", cost=cost, team_id=(player_id % 8) + 1))
    for player_id in FORWARDS:
        squad.append(make_player(player_id, "FWD", cost=cost, team_id=(player_id % 8) + 1))

    return squad


def squad_ids():
    return GOALKEEPERS + DEFENDERS + MIDFIELDERS + FORWARDS


def test_a_simple_swap_is_allowed(session):
    add_players(session, build_squad(cost=5.0))  # 75m spent, plenty of room
    add_players(session, [make_player(100, "DEF", cost=6.0, team_id=1)])

    result = call_propose_changes([{"out_id": 3, "in_id": 100}], squad_ids(), session)

    assert result["valid"] is True
    assert result["changes"][0]["in_id"] == 100
    assert result["changes"][0]["out_id"] == 3


def test_two_swaps_that_fit_alone_but_not_together_are_rejected(session):
    # the key case: 15 x 6.6 = 99.0m, so only 1.0m of room. Each swap adds 0.8m -
    # fine on its own, but together they add 1.6m and go over
    add_players(session, build_squad(cost=6.6))
    add_players(session, [
        make_player(100, "DEF", cost=7.4, team_id=1),
        make_player(101, "DEF", cost=7.4, team_id=1),
    ])

    first_alone = call_propose_changes([{"out_id": 3, "in_id": 100}], squad_ids(), session)
    second_alone = call_propose_changes([{"out_id": 4, "in_id": 101}], squad_ids(), session)

    both_together = call_propose_changes(
        [{"out_id": 3, "in_id": 100}, {"out_id": 4, "in_id": 101}], squad_ids(), session
    )

    assert first_alone["valid"] is True
    assert second_alone["valid"] is True
    assert both_together["valid"] is False
    assert "budget" in both_together["errors"][0]


def test_an_imported_budget_above_100m_is_respected(session):
    # squad worth 105.0m (15 x 7.0) - over 100m, but it's an imported team so the
    # frontend sends squad value + bank = 105.5m. A +0.5m swap just fits
    add_players(session, build_squad(cost=7.0))
    add_players(session, [make_player(100, "DEF", cost=7.5, team_id=1)])

    with_imported_budget = call_propose_changes(
        [{"out_id": 3, "in_id": 100}], squad_ids(), session, budget=105.5
    )
    with_default_budget = call_propose_changes(
        [{"out_id": 3, "in_id": 100}], squad_ids(), session
    )

    assert with_imported_budget["valid"] is True
    assert with_default_budget["valid"] is False  # strict 100m for a hand-built squad


def test_positions_must_match(session):
    add_players(session, build_squad(cost=5.0))
    add_players(session, [make_player(100, "DEF", cost=5.0, team_id=1)])

    # goalkeeper out, defender in
    result = call_propose_changes([{"out_id": 1, "in_id": 100}], squad_ids(), session)

    assert result["valid"] is False
    assert "positions must match" in result["errors"][0]


def test_a_fourth_player_from_one_club_is_rejected(session):
    # team 2 already has 2 players (ids 1 and 9) - bringing in 2 more makes 4
    add_players(session, build_squad(cost=5.0))
    add_players(session, [
        make_player(100, "DEF", cost=5.0, team_id=2),
        make_player(101, "DEF", cost=5.0, team_id=2),
    ])

    result = call_propose_changes(
        [{"out_id": 3, "in_id": 100}, {"out_id": 4, "in_id": 101}], squad_ids(), session
    )

    assert result["valid"] is False
    assert "from one club" in result["errors"][0]


def test_cannot_bring_in_someone_already_in_the_squad(session):
    add_players(session, build_squad(cost=5.0))

    result = call_propose_changes([{"out_id": 3, "in_id": 5}], squad_ids(), session)

    assert result["valid"] is False
    assert "already in the squad" in result["errors"][0]


def test_filling_an_empty_slot_is_allowed(session):
    add_players(session, build_squad(cost=5.0))
    add_players(session, [make_player(100, "DEF", cost=5.0, team_id=1)])

    # squad is missing defender 7, so there's an empty DEF slot to fill
    squad_missing_a_defender = [player_id for player_id in squad_ids() if player_id != 7]

    result = call_propose_changes([{"out_id": None, "in_id": 100}], squad_missing_a_defender, session)

    assert result["valid"] is True
    assert result["changes"][0]["out_name"] is None


def test_adding_to_a_full_position_is_rejected(session):
    # nobody going out, but all 5 defenders are already picked - would make 6
    add_players(session, build_squad(cost=5.0))
    add_players(session, [make_player(100, "DEF", cost=5.0, team_id=1)])

    result = call_propose_changes([{"out_id": None, "in_id": 100}], squad_ids(), session)

    assert result["valid"] is False
    assert "max is 5" in result["errors"][0]
