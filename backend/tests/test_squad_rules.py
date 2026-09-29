from conftest import make_player, make_squad
from recommend_player import get_squad_completeness, count_by_club


def test_empty_squad_is_short_in_every_position():
    completeness = get_squad_completeness([])

    assert completeness["GKP"] == {"filled": 0, "required": 2, "missing": 2}
    assert completeness["DEF"] == {"filled": 0, "required": 5, "missing": 5}
    assert completeness["MID"] == {"filled": 0, "required": 5, "missing": 5}
    assert completeness["FWD"] == {"filled": 0, "required": 3, "missing": 3}


def test_full_squad_is_missing_nothing():
    completeness = get_squad_completeness(make_squad({"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}))

    assert all(counts["missing"] == 0 for counts in completeness.values())


def test_partly_built_squad_reports_only_what_is_short():
    # 2 keepers and 2 defenders picked, nothing else
    completeness = get_squad_completeness(make_squad({"GKP": 2, "DEF": 2}))

    assert completeness["GKP"]["missing"] == 0
    assert completeness["DEF"]["missing"] == 3
    assert completeness["MID"]["missing"] == 5


def test_over_filled_position_reports_missing_zero_not_negative():
    # 6 defenders when only 5 are allowed - "missing" should floor at 0
    completeness = get_squad_completeness(make_squad({"DEF": 6}))

    assert completeness["DEF"]["filled"] == 6
    assert completeness["DEF"]["missing"] == 0


def test_completeness_always_covers_all_four_positions():
    # even for an empty squad - this is the whole reason the helper exists, since
    # find_weakest_by_position can only ever report on positions that have players
    assert set(get_squad_completeness([])) == {"GKP", "DEF", "MID", "FWD"}


def test_count_by_club_tallies_players_per_team():
    players = [
        make_player(1, "DEF", team_id=1),
        make_player(2, "DEF", team_id=1),
        make_player(3, "MID", team_id=2),
    ]

    assert count_by_club(players) == {1: 2, 2: 1}


def test_count_by_club_of_empty_squad_is_empty():
    assert count_by_club([]) == {}
