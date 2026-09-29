"""
Pulls the FPL data into the local database.

Two ways in:
  refresh_data()     - always refreshes, used by "python load_data.py"
  refresh_if_stale() - only refreshes if the data is older than MAX_DATA_AGE,
                       which is what server.py calls on startup

Everything is written with session.merge rather than session.add. add only ever
INSERTS, so re-running it over an existing database failed on duplicate primary
keys - the only way to refresh used to be deleting fpl_advisor.db first. merge
updates a row if its primary key already exists and inserts it if not, so this
is now safe to run over and over: it picks up changed prices, points and form,
and adds players who are new to the game since the last run.
"""

from sqlalchemy.orm import sessionmaker
from models import (
    Base, Player, Team, Fixture, DataRefresh,
    GoalkeeperStats, DefenderStats, MidfielderStats, ForwardStats,
)
from db import engine
from get_data import get_default_data, get_fixture_data
from datetime import datetime, timedelta

Positions = {
    1: "GKP",
    2: "DEF",
    3: "MID",
    4: "FWD",
}

# how stale the data is allowed to get before a startup refresh kicks in - data refreshed every 12 hr
MAX_DATA_AGE = timedelta(hours=12)

# Session tracks what you want to add to the database, until you commit
# nothing is added. 
Session = sessionmaker(bind=engine)


def get_last_refresh(session):
    # None if the data has never been loaded
    row = session.get(DataRefresh, 1)
    return row.refreshed_at if row else None


def refresh_data():
    session = Session()

    fpl_data = get_default_data()
    fixtures = get_fixture_data()

    for team_data in fpl_data["teams"]:
        team = Team(
            id=team_data["id"],
            name=team_data["name"],
            short_name=team_data["short_name"],
        )
        session.merge(team)

    for fixture_data in fixtures:

        # need to .replace("Z", "+00:00") as date is sent in this format "2026-08-15T19:00:00Z"
        # and datetime expects an actutal date time, not a string. ==> date time allows for real date time comparisons 
        kickoff_raw = fixture_data["kickoff_time"]

        # need to check if it exists, some games dates are yet to be determined. 
        if kickoff_raw is not None:
            kickoff = datetime.fromisoformat(kickoff_raw)
        else:
            kickoff = None

        fixture = Fixture(
            id=fixture_data["id"],
            gameweek=fixture_data["event"],
            date=kickoff,
            home_team=fixture_data["team_h"],
            away_team=fixture_data["team_a"],
            team_h_difficulty=fixture_data["team_h_difficulty"],
            team_a_difficulty=fixture_data["team_a_difficulty"],
            finished=fixture_data["finished"],
        )
        session.merge(fixture)

    for element in fpl_data["elements"]:

        position = Positions[element["element_type"]]

        player = Player(
            id=element["id"],
            first_name=element["first_name"],
            second_name=element["second_name"],
            team_id=element["team"],
            position=Positions[element["element_type"]],
            now_cost=element["now_cost"] / 10,   # FPL stores price as 125 meaning 12.5m
            total_points=element["total_points"],
            form=float(element["form"]),
        )
        session.merge(player)

        if position == "GKP":
            session.merge(GoalkeeperStats(
                player_id=element["id"],
                saves=element["saves"],
                clean_sheets=element["clean_sheets"],
                goals_conceded=element["goals_conceded"],
                penalties_saved=element["penalties_saved"],
                yellow_cards=element["yellow_cards"],
                red_cards=element["red_cards"]
            ))

        elif position == "DEF":
            session.merge(DefenderStats(
                player_id=element["id"],
                clean_sheets=element["clean_sheets"],
                goals_conceded=element["goals_conceded"],
                expected_goals_conceded=float(element["expected_goals_conceded"]),
                own_goals=element["own_goals"],
                yellow_cards=element["yellow_cards"],
                red_cards=element["red_cards"],
                goals_scored=element["goals_scored"],
                assists=element["assists"],
            ))

        elif position == "MID":
            session.merge(MidfielderStats(
                player_id=element["id"],
                goals_scored=element["goals_scored"],
                assists=element["assists"],
                expected_goals=float(element["expected_goals"]),
                expected_assists=float(element["expected_assists"]),
                creativity=float(element["creativity"]),
                yellow_cards=element["yellow_cards"],
                red_cards=element["red_cards"],
                clean_sheets=element["clean_sheets"]
            ))

        elif position == "FWD":
            session.merge(ForwardStats(
                player_id=element["id"],
                goals_scored=element["goals_scored"],
                expected_goals=float(element["expected_goals"]),
                threat=float(element["threat"]),
                penalties_missed=element["penalties_missed"],
                yellow_cards=element["yellow_cards"],
                red_cards=element["red_cards"],
                assists=element["assists"]
            ))

    # stamped last, so a run that falls over partway doesn't look like a success
    session.merge(DataRefresh(id=1, refreshed_at=datetime.now()))

    session.commit() #writes the data into the database
    session.close()

    return len(fpl_data["elements"])


def refresh_checker():
    # returns True if it actually refreshed, False if the data was fresh enough
    session = Session()
    last_refresh = get_last_refresh(session)
    session.close()

    if last_refresh is not None and datetime.now() - last_refresh < MAX_DATA_AGE:
        return False

    refresh_data()
    return True


if __name__ == "__main__":
    count = refresh_data()
    print(f"Refreshed {count} players.")
