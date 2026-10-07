# tests the budget rule: money left = budget - what the squad costs.
# budget is 100m for a squad built by hand, or whatever the frontend sends for
# an imported one (squad value + bank). Money is also held back for empty slots

import pytest

from conftest import make_player, add_players
from recommend_player import get_max_price_for_slot, recommend_for_slot, BUDGET_LIMIT


def build(counts, start_id, cost):
    players, next_id = [], start_id

    for position, count in counts.items():
        for _ in range(count):
            players.append(make_player(next_id, position, cost=cost, team_id=(next_id % 8) + 1))
            next_id += 1

    return players


def test_empty_squad_has_exactly_100m(session):
    add_players(session, build({"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}, 100, cost=4.0))

    budget_remaining, _ = get_max_price_for_slot("GKP", [], [], session)

    assert budget_remaining == pytest.approx(BUDGET_LIMIT)


def test_budget_remaining_is_what_is_left_after_what_is_spent(session):
    squad = build({"GKP": 2}, 1, cost=6.0)  # 12.0m spent
    add_players(session, squad)

    budget_remaining, _ = get_max_price_for_slot(
        "DEF", squad, [player.id for player in squad], session
    )

    assert budget_remaining == pytest.approx(BUDGET_LIMIT - 12.0)


def test_an_imported_budget_above_100m_is_used(session):
    # an imported squad worth 105.0m (prices rose) with 0.5m in the bank -
    # the frontend sends 105.5m, so there's 0.5m left, not -5.0m
    squad = build({"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}, 1, cost=7.0)
    add_players(session, squad)

    budget_remaining, _ = get_max_price_for_slot(
        "DEF", squad, [player.id for player in squad], session, budget=105.5
    )

    assert budget_remaining == pytest.approx(0.5)


def test_a_hand_built_squad_over_100m_has_negative_money_left(session):
    # same 105.0m squad, but no budget sent, so the strict 100m applies
    squad = build({"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}, 1, cost=7.0)
    add_players(session, squad)

    budget_remaining, _ = get_max_price_for_slot(
        "DEF", squad, [player.id for player in squad], session
    )

    assert budget_remaining == pytest.approx(-5.0)


def test_money_is_reserved_for_other_empty_slots_but_not_this_one(session):
    # nothing picked yet, and every available player costs 4.0. Filling one slot
    # means holding back for the OTHER 14, not all 15
    available_cost = 4.0
    add_players(session, build({"GKP": 4, "DEF": 6, "MID": 6, "FWD": 4}, 100, cost=available_cost))

    _, max_price = get_max_price_for_slot("GKP", [], [], session)

    slots_still_to_fill = 15 - 1
    assert max_price == pytest.approx(BUDGET_LIMIT - slots_still_to_fill * available_cost)


def test_each_position_reserves_its_own_cheapest_player(session):

    add_players(session, build({"GKP": 2}, 100, cost=4.0) + build({"FWD": 3}, 200, cost=9.0))

    # squad needs 2 GKP and 3 FWD; filling a GKP slot reserves 1 GKP + 3 FWD
    _, max_price = get_max_price_for_slot("GKP", [], [], session)

    expected_reserved = (1 * 4.0) + (3 * 9.0)  # DEF/MID have no players available, so reserve 0
    assert max_price == pytest.approx(BUDGET_LIMIT - expected_reserved)


def test_an_overcommitted_squad_gives_no_suggestions_rather_than_an_error(session):
    # 10 expensive players picked, 5 slots still empty and not enough left for any players

    squad = build({"GKP": 2, "DEF": 5, "MID": 3}, 1, cost=9.0)
    pool = build({"MID": 3, "FWD": 3}, 100, cost=8.0)
    add_players(session, squad + pool)

    squad_ids = [player.id for player in squad]

    _, max_price = get_max_price_for_slot("MID", squad, squad_ids, session)
    assert max_price < 0

    result = recommend_for_slot(
        "MID", squad_ids, session,
        all_scores={player.id: 50.0 for player in squad + pool},
    )

    assert result["suggestions"] == []
    assert result["max_price_for_slot"] == pytest.approx(max_price, abs=0.05)
