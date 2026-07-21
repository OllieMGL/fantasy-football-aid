from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime
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

class Fixture(Base):
    __tablename__ = "fixtures"

    id = Column(Integer, primary_key=True)
    gameweek = Column(Integer) 
    date = Column(DateTime) # date time - stores as an actual date 
    home_team = Column(Integer, ForeignKey("teams.id"))
    away_team = Column(Integer, ForeignKey("teams.id"))
    team_h_difficulty = Column(Integer)
    team_a_difficulty = Column(Integer)
    finished = Column(Boolean)



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
    
    goalkeeper_stats = relationship("GoalkeeperStats", uselist=False)
    defender_stats = relationship("DefenderStats", uselist=False)
    midfielder_stats = relationship("MidfielderStats", uselist=False)
    forward_stats = relationship("ForwardStats", uselist=False)


class GoalkeeperStats(Base):
    __tablename__ = "goalkeeper_stats"

    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    saves = Column(Integer)
    clean_sheets = Column(Integer)
    goals_conceded = Column(Integer)
    penalties_saved = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)


class DefenderStats(Base):
    __tablename__ = "defender_stats"

    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    clean_sheets = Column(Integer)
    goals_conceded = Column(Integer)
    expected_goals_conceded = Column(Float)
    own_goals = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)


class MidfielderStats(Base):
    __tablename__ = "midfielder_stats"

    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    goals_scored = Column(Integer)
    assists = Column(Integer)
    expected_goals = Column(Float)
    expected_assists = Column(Float)
    creativity = Column(Float)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)


class ForwardStats(Base):
    __tablename__ = "forward_stats"

    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    goals_scored = Column(Integer)
    expected_goals = Column(Float)
    threat = Column(Float)
    penalties_missed = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)