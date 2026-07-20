from sqlalchemy import create_engine
from models import Base, Player, Team

engine = create_engine("sqlite:///fpl_advisor.db") # sets up the connection to SQLlite

Base.metadata.create_all(engine) # creates the database that matches the one in models.py