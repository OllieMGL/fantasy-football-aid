from sqlalchemy.orm import sessionmaker
from db import engine
from scorers.goalkeeper_scorer import get_goalkeepers, score_all_goalkeepers


def main():
    Session = sessionmaker(bind=engine)
    session = Session()

    goalkeepers = get_goalkeepers(session)
    goalkeeper_scores = score_all_goalkeepers(session)

    for p in goalkeepers:
        print(p.first_name, p.second_name, "-", goalkeeper_scores[p.id])


main()