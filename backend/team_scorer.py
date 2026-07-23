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


def check_valid_team(players):
    errors = []

    if len(players) != 15:
        errors.append(f"Team must have exactly 15 players (found {len(players)}).")

    required_counts = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
    position_counts = {"GKP": 0, "DEF": 0, "MID": 0, "FWD": 0}

    for player in players:
        position_counts[player.position] += 1

    for position, required in required_counts.items():
        if position_counts[position] != required:
            errors.append(f"Need {required} {position}, but found {position_counts[position]}.")

    total_cost = sum(p.now_cost for p in players)
    if total_cost > 100.0:
        errors.append(f"Team costs £{total_cost:.1f}m, which is over the £100.0m budget.")

    team_counts = {}
    for player in players:
        if player.team_id not in team_counts:
            team_counts[player.team_id] = 1
        else:
            team_counts[player.team_id] = team_counts[player.team_id] + 1

    for team_id, count in team_counts.items():
        if count > 3:
            errors.append(f"Too many players from team_id {team_id} ({count}, max is 3).")

    return errors


def main():
    selected_player_ids = [82, 201, 505, 31, 154, 480, 397, 165, 411, 346, 497, 539, 423, 338, 40]

    Session = sessionmaker(bind=engine)
    session = Session()

    team_players = get_players_by_ids(selected_player_ids, session)

    errors = check_valid_team(team_players)
    if errors:
        print("Team is invalid:")
        for error in errors:
            print(" -", error)
        return

    team_average = score_team(selected_player_ids, session)

    for p in team_players:
        print(p.first_name, p.second_name)

    print(f"\nOverall team score: {team_average}/100")


main()