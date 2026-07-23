from sqlalchemy.orm import sessionmaker
from models import Base, Player, Team, Fixture, GoalkeeperStats, DefenderStats, MidfielderStats, ForwardStats
from db import engine
from get_data import get_default_data, get_fixture_data
from datetime import datetime

Positions = {
    1: "GKP",
    2: "DEF",
    3: "MID",
    4: "FWD",
}

# Session tracks what you want to add to the database, until you commit
# nothing is added. 
Session = sessionmaker(bind=engine) 
session = Session()

fpl_data = get_default_data()
fixture_data = get_fixture_data()

for team_data in fpl_data["teams"]:
    team = Team(
        id=team_data["id"],
        name=team_data["name"],
        short_name=team_data["short_name"],
    )
    session.add(team)


for fixture_data in fixture_data:

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
    session.add(fixture)


for element in fpl_data["elements"]:

    position = Positions[element["element_type"]]

    player = Player(
        id=element["id"],
        first_name=element["first_name"],
        second_name=element["second_name"],
        team_id=element["team"],
        position=Positions[element["element_type"]],
        now_cost=element["now_cost"] / 10,   # FPL stores price as 125 meaning £12.5m
        total_points=element["total_points"],
        form=float(element["form"]),
    )
    session.add(player)

    if position == "GKP":
        session.add(GoalkeeperStats(
            player_id=element["id"],
            saves=element["saves"],
            clean_sheets=element["clean_sheets"],
            goals_conceded=element["goals_conceded"],
            penalties_saved=element["penalties_saved"],
            yellow_cards=element["yellow_cards"],
            red_cards=element["red_cards"]
        ))

    elif position == "DEF":
        session.add(DefenderStats(
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
        session.add(MidfielderStats(
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
        session.add(ForwardStats(
            player_id=element["id"],
            goals_scored=element["goals_scored"],
            expected_goals=float(element["expected_goals"]),
            threat=float(element["threat"]),
            penalties_missed=element["penalties_missed"],
            yellow_cards=element["yellow_cards"],
            red_cards=element["red_cards"]
        ))




session.commit() #writes the data into the database


print(f"Inserted {len(fpl_data['elements'])} players.")