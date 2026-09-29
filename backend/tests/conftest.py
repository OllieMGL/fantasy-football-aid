"""
Shared setup for the tests.

Two things worth knowing about how these tests are built:

1. They never touch fpl_advisor.db. Each test gets its own empty in-memory
   SQLite database, so tests can't interfere with each other and can't be
   broken by a data refresh changing real prices underneath them.

2. Test players are deliberately tiny and made up. Real FPL data changes every
   day, so asserting anything against it would give tests that pass today and
   fail tomorrow for no reason.
"""

import os
import sys

# so the tests can import the backend modules the same way the app does
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Player, Team


@pytest.fixture
def session():
    # built fresh for every test
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    test_session = sessionmaker(bind=engine)()

    # eight clubs, because a legal 15-player squad needs at least five to stay
    # under the 3-per-club cap - fewer, and every replacement silently gets
    # filtered out as club-capped and tests pass for the wrong reason
    test_session.add_all([
        Team(id=team_id, name=f"Team {team_id}", short_name=f"T{team_id}")
        for team_id in range(1, 9)
    ])
    test_session.commit()

    yield test_session
    test_session.close()

# makes test player
def make_player(player_id, position, cost=5.0, team_id=1):
    
    return Player(
        id=player_id,
        first_name="Test",
        second_name=f"Player{player_id}",
        team_id=team_id,
        position=position,
        now_cost=cost,
        total_points=0,
        form=0.0,
    )


# makes test squad
def make_squad(positions, cost=5.0, team_id=1):

    players = []
    next_id = 1

    for position, count in positions.items():
        for _ in range(count):
            players.append(make_player(next_id, position, cost=cost, team_id=team_id))
            next_id += 1

    return players


def add_players(session, players):
    """make_player returns an unsaved object - anything that queries the
    database needs the rows actually written first."""
    session.add_all(players)
    session.commit()
    return players
