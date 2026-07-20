from sqlalchemy.orm import sessionmaker
from models import Base, Player, Team
from db import engine
from get_default_player_data import get_default_player_data  

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

fpl_data = get_default_player_data()

for team_data in fpl_data["teams"]:
    team = Team(
        id=team_data["id"],
        name=team_data["name"],
        short_name=team_data["short_name"],
    )
    session.add(team)


for element in fpl_data["elements"]:
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

session.commit() #writes the data into the database

print(f"Inserted {len(fpl_data['elements'])} players.")