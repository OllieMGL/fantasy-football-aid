from sqlalchemy.orm import sessionmaker
from models import Base, Player
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

for element in fpl_data["elements"]:
    player = Player(
        id=element["id"],
        web_name=element["web_name"],
        team=element["team"],
        position=Positions[element["element_type"]],
        now_cost=element["now_cost"] / 10,   # FPL stores price as 125 meaning £12.5m
        total_points=element["total_points"],
        form=float(element["form"]),
    )
    session.add(player)

session.commit() #writes the data into the database

print(f"Inserted {len(fpl_data['elements'])} players.")