from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    web_name = Column(String)
    team = Column(Integer)
    position = Column(String)
    now_cost = Column(Float)
    total_points = Column(Integer)
    form = Column(Float)