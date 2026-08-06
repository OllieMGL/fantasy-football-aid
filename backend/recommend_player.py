from sqlalchemy.orm import sessionmaker
from db import engine
from scorers.goalkeeper_scorer import score_all_goalkeepers
from scorers.defender_scorer import score_all_defenders
from scorers.midfielder_scorer import score_all_midfielders
from scorers.forward_scorer import score_all_forwards
from team_scorer import get_players_by_ids
from models import Player

def get_all_scores(session):

    goalkeeper_scores = score_all_goalkeepers(session)
    defender_scores = score_all_defenders(session)
    midfielder_scores = score_all_midfielders(session)
    forward_scores = score_all_forwards(session)

    all_scores = {}
    all_scores.update(goalkeeper_scores)
    all_scores.update(defender_scores)
    all_scores.update(midfielder_scores)
    all_scores.update(forward_scores)

    return all_scores

def find_weakest_by_position(team_players, player_scores):
    weakest = {}

    for player in team_players:
        position = player.position
        score = player_scores[player.id]

        if position not in weakest or score < player_scores[weakest[position].id]:
            weakest[position] = player

    return weakest


def get_score_for(player, all_scores):
    return all_scores[player.id]


def find_replacement(weak_player, session, all_scores, current_team_ids):
    
    min_price = weak_player.now_cost - 1
    max_price = weak_player.now_cost + 1

    candidates = (
        session.query(Player)
        .filter(
            Player.position == weak_player.position,
            Player.now_cost >= min_price,
            Player.now_cost <= max_price,
            Player.id.notin_(current_team_ids),
        )
        .all()
    )

    if not candidates:
        return None

    best_candidate = max(candidates, key=get_score_for)

    weak_player_score = all_scores[weak_player.id]
    best_candidate_score = all_scores[best_candidate.id]

    if best_candidate_score <= weak_player_score:
        return None

    return best_candidate


def get_recommendations(selected_player_ids, session):

    team_players = get_players_by_ids(selected_player_ids, session)
    all_scores = get_all_scores(session)
    weakest_by_position = find_weakest_by_position(team_players, all_scores)

    recommendations = {}

    for position, weak_player in weakest_by_position.items():
        replacement = find_replacement(weak_player, session, all_scores, selected_player_ids)

        recommendations[position] = {
            "current_player": weak_player,
            "current_score": all_scores[weak_player.id],
            "suggested_replacement": replacement,
            "suggested_score": all_scores[replacement.id] if replacement else None,
        }

    return recommendations