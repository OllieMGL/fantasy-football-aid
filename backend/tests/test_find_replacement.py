#Tests for find_replacement - the "upgrade" half of the recommendations.

from conftest import make_player, add_players
from recommend_player import (
    find_replacement, count_by_club, MAX_PER_CLUB, REPLACEMENT_PRICE_WINDOW,
)


def test_picks_the_highest_scoring_candidate(session):

    weak = make_player(1, "DEF", cost=5.0, team_id=1)
    ok = make_player(10, "DEF", cost=5.0, team_id=2)
    better = make_player(11, "DEF", cost=5.0, team_id=3)
    add_players(session, [weak, ok, better])

    result = find_replacement(
        weak, session,
        all_scores={1: 10.0, 10: 60.0, 11: 80.0},
        current_team_ids=[1],
        club_counts=count_by_club([weak]),
    )

    assert result.id == better.id


def test_returns_none_when_nothing_scores_higher(session):
    weak = make_player(1, "DEF", cost=5.0, team_id=1)
    worse = make_player(10, "DEF", cost=5.0, team_id=2)
    add_players(session, [weak, worse])

    result = find_replacement(
        weak, session,
        all_scores={1: 50.0, 10: 40.0},
        current_team_ids=[1],
        club_counts=count_by_club([weak]),
    )

    assert result is None


def test_an_exact_tie_is_not_an_upgrade(session):
    # checks for a strict improvement - swapping for an equally good player

    weak = make_player(1, "DEF", cost=5.0, team_id=1)
    same = make_player(10, "DEF", cost=5.0, team_id=2)
    add_players(session, [weak, same])

    result = find_replacement(
        weak, session,
        all_scores={1: 50.0, 10: 50.0},
        current_team_ids=[1],
        club_counts=count_by_club([weak]),
    )

    assert result is None


def test_skips_a_club_already_at_the_cap(session):

    weak = make_player(1, "DEF", cost=5.0, team_id=1)
    at_cap = [make_player(2 + i, "MID", cost=5.0, team_id=2) for i in range(MAX_PER_CLUB)] # fills players to max squad cap

    capped_club_star = make_player(10, "DEF", cost=5.0, team_id=2)
    other_club = make_player(11, "DEF", cost=5.0, team_id=3)

    squad = [weak] + at_cap
    add_players(session, squad + [capped_club_star, other_club])

    result = find_replacement(
        weak, session,
        all_scores={1: 10.0, 10: 99.0, 11: 50.0, **{p.id: 50.0 for p in at_cap}},
        current_team_ids=[p.id for p in squad],
        club_counts=count_by_club(squad),
    )

    # the higher-scoring team 2 player is unavailable, so it falls to team 3
    assert result.id == other_club.id


def test_allows_a_same_club_swap_even_at_the_cap(session):

    weak = make_player(1, "DEF", cost=5.0, team_id=1)
    other_team_1 = [make_player(2 + i, "MID", cost=5.0, team_id=1) for i in range(MAX_PER_CLUB - 1)]

    same_club_upgrade = make_player(10, "DEF", cost=5.0, team_id=1)

    squad = [weak] + other_team_1
    add_players(session, squad + [same_club_upgrade])

    assert count_by_club(squad)[1] == MAX_PER_CLUB  #

    result = find_replacement(
        weak, session,
        all_scores={1: 10.0, 10: 90.0, **{p.id: 50.0 for p in other_team_1}},
        current_team_ids=[p.id for p in squad],
        club_counts=count_by_club(squad),
    )

    assert result is not None, "dropping a player should free up their own club slot"
    assert result.id == same_club_upgrade.id


def test_includes_a_player_exactly_at_the_edge_of_the_price_window(session):

    weak = make_player(1, "DEF", cost=5.0, team_id=1)
    dearest_allowed = make_player(10, "DEF", cost=5.0 + REPLACEMENT_PRICE_WINDOW, team_id=2)
    add_players(session, [weak, dearest_allowed])

    result = find_replacement(
        weak, session,
        all_scores={1: 10.0, 10: 90.0},
        current_team_ids=[1],
        club_counts=count_by_club([weak]),
    )

    assert result.id == dearest_allowed.id


def test_ignores_a_player_outside_the_price_window(session):

    weak = make_player(1, "DEF", cost=5.0, team_id=1)
    too_expensive = make_player(10, "DEF", cost=5.0 + REPLACEMENT_PRICE_WINDOW + 0.1, team_id=2)
    add_players(session, [weak, too_expensive])

    result = find_replacement(
        weak, session,
        all_scores={1: 10.0, 10: 99.0},
        current_team_ids=[1],
        club_counts=count_by_club([weak]),
    )

    assert result is None


def test_ignores_a_player_you_cannot_afford(session):
    # the better player is inside the ±0.5m window, but with only 0.2m left
    # the most we can pay is 5.0 + 0.2 = 5.2m
    weak = make_player(1, "DEF", cost=5.0, team_id=1)
    too_dear = make_player(10, "DEF", cost=5.5, team_id=2)
    add_players(session, [weak, too_dear])

    result = find_replacement(
        weak, session,
        all_scores={1: 10.0, 10: 99.0},
        current_team_ids=[1],
        club_counts=count_by_club([weak]),
        money_left=0.2,
    )

    assert result is None


def test_never_suggests_a_player_already_in_the_squad(session):
    weak = make_player(1, "DEF", cost=5.0, team_id=1)
    already_owned = make_player(2, "DEF", cost=5.0, team_id=2)
    add_players(session, [weak, already_owned])

    result = find_replacement(
        weak, session,
        all_scores={1: 10.0, 2: 99.0},
        current_team_ids=[1, 2],
        club_counts=count_by_club([weak, already_owned]),
    )

    assert result is None
