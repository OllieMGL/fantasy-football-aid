from sqlalchemy.orm import sessionmaker
from db import engine
from scorers.goalkeeper_scorer import get_goalkeepers, score_all_goalkeepers
from scorers.defender_scorer import get_defenders, score_all_defenders
from scorers.midfielder_scorer import get_midfielders, score_all_midfielders
from scorers.forward_scorer import get_forwards, score_all_forwards



def main():
    Session = sessionmaker(bind=engine)
    session = Session()

    goalkeepers = get_goalkeepers(session)
    goalkeeper_scores = score_all_goalkeepers(session)

    defenders = get_defenders(session)
    defender_scores = score_all_defenders(session)

    midfielders = get_midfielders(session)
    midfielder_scores = score_all_midfielders(session)
        
    forwards = get_forwards(session)
    forward_scores = score_all_forwards(session)

    for p in goalkeepers:
        print(p.first_name, p.second_name, "-", goalkeeper_scores[p.id])

    # for p in defenders:
    #     print(p.first_name, p.second_name, "-", defender_scores[p.id])

    # for p in midfielders:
    #     print(p.first_name, p.second_name, "-", midfielder_scores[p.id])



    # sorted_forwards = sorted(forward_scores.items(), key=lambda item: item[1], reverse=True)
    # top_20_forwards = sorted_forwards[:20]

    # forwards_by_id = {p.id: p for p in forwards}

    # for player_id, score in top_20_forwards:
    #     player = forwards_by_id[player_id]
    #     print(player.first_name, player.second_name, "-", score)

main()