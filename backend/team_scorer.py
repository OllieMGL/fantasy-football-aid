from sqlalchemy.orm import sessionmaker
from db import engine
from models import Player
from scorers.goalkeeper_scorer import score_all_goalkeepers
from scorers.defender_scorer import score_all_defenders
from scorers.midfielder_scorer import score_all_midfielders
from scorers.forward_scorer import score_all_forwards

def get_players_by_ids(player_ids, session):
    players = (
        session.query(Player)
        .filter(Player.id.in_(player_ids))
        .all()
    )
    return players


def score_team(player_ids, session):
    team_players = get_players_by_ids(player_ids, session)

    goalkeeper_scores = score_all_goalkeepers(session)
    defender_scores = score_all_defenders(session)
    midfielder_scores = score_all_midfielders(session)
    forward_scores = score_all_forwards(session)

    all_scores = {}
    all_scores.update(goalkeeper_scores)
    all_scores.update(defender_scores)
    all_scores.update(midfielder_scores)
    all_scores.update(forward_scores)

    player_scores = {}
    for player in team_players:
        player_scores[player.id] = all_scores[player.id]

    team_average = sum(player_scores.values()) / len(player_scores)

    return round(team_average, 1)


def main():

    selected_player_ids = [82, 377, 505, 31, 154, 480, 397, 165, 411, 346, 497, 539, 388] 

    Session = sessionmaker(bind=engine)
    session = Session()

    team_average = score_team(selected_player_ids, session)

    team_players = get_players_by_ids(selected_player_ids, session)
    for p in team_players:
        print(p.first_name, p.second_name)
        
    print(f"\nOverall team score: {team_average}/100")


main()

