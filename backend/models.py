from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    short_name = Column(String)

    # allows you to write some_team.players - list of players in a team 
    #back_populates just lets SQL know they are in same relationship - keep them in sync
    players = relationship("Player", back_populates="team")




class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    second_name = Column(String)
    team_id = Column(Integer, ForeignKey("teams.id"))
    position = Column(String)
    now_cost = Column(Float)
    total_points = Column(Integer)
    form = Column(Float)

    # allows you to write something like some_player.team... 
    team = relationship("Team", back_populates="players")