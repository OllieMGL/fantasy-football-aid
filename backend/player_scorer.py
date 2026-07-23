from sqlalchemy.orm import sessionmaker
from db import engine
from scorers.goalkeeper_scorer import get_goalkeepers, score_all_goalkeepers
from scorers.defender_scorer import get_defenders, score_all_defenders


def main():
    Session = sessionmaker(bind=engine)
    session = Session()

    goalkeepers = get_goalkeepers(session)
    goalkeeper_scores = score_all_goalkeepers(session)

    defenders = get_defenders(session)
    defender_scores = score_all_defenders(session)

    # for p in goalkeepers:
    #     print(p.first_name, p.second_name, "-", goalkeeper_scores[p.id])


    for p in defenders:
        print(p.first_name, p.second_name, "-", defender_scores[p.id])


main()