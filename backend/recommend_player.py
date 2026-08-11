from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from db import engine
from scorers.goalkeeper_scorer import score_all_goalkeepers
from scorers.defender_scorer import score_all_defenders
from scorers.midfielder_scorer import score_all_midfielders
from scorers.forward_scorer import score_all_forwards
from team_scorer import get_players_by_ids
from models import Player

REQUIRED_COUNTS = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
BUDGET_LIMIT = 100.0
MAX_PER_CLUB = 3
SLOT_SUGGESTION_COUNT = 4

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
    # will return a dictionary of..
    # POSITION : Weakest player 
    #e.g GKP : Kepa
    weakest = {}

    for player in team_players:
        position = player.position
        score = player_scores[player.id]

        if position not in weakest or score < player_scores[weakest[position].id]:
            weakest[position] = player

    return weakest

def find_replacement(weak_player, session, all_scores, current_team_ids):
    
    min_price = weak_player.now_cost - 0.5
    max_price = weak_player.now_cost + 0.5

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

    def get_score_for(candidate):
        return all_scores[candidate.id]

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
    # recommendations creates a nested dictionary - dictionary inside a dictionary 
    # Key is position and the value is another dictionary containing the infomation below

    for position, weak_player in weakest_by_position.items():
        replacement = find_replacement(weak_player, session, all_scores, selected_player_ids)

        recommendations[position] = {
            "current_player": weak_player,
            "current_score": all_scores[weak_player.id],
            "suggested_replacement": replacement,
            "suggested_score": all_scores[replacement.id] if replacement else None,
        }

    return recommendations


# used to find the cheapest available player
# used below to work out how much money must stay reserved for other empty slots
def get_min_available_cost_by_position(excluded_ids, session):
    rows = (
        session.query(Player.position, func.min(Player.now_cost))
        .filter(Player.id.notin_(excluded_ids))
        .group_by(Player.position)
        .all()
    )
    return dict(rows)  # e.g. {"GKP": 4.0, "DEF": 3.9, "MID": 4.3, "FWD": 4.0}


def recommend_for_slot(position, other_player_ids, session):

    other_players = get_players_by_ids(other_player_ids, session)

    position_counts = {p: 0 for p in REQUIRED_COUNTS}
    club_counts = {}
    amount_spent = 0.0

    for player in other_players:
        position_counts[player.position] += 1 # checks correct postions 
        club_counts[player.team_id] = club_counts.get(player.team_id, 0) + 1 # checks 3 per club, defaults to 0 if club not in dict 
        amount_spent += player.now_cost 

    budget_remaining = BUDGET_LIMIT - amount_spent


    min_cost_by_position = get_min_available_cost_by_position(other_player_ids, session)

    reserved_for_other_slots = 0.0
    for pos, required in REQUIRED_COUNTS.items():
        empty_slots = required - position_counts[pos] # how many players needed - how many have been filled
        if pos == position:
            empty_slots -= 1  # dont need to reserve money for the position you are recommending for
        empty_slots = max(0, empty_slots) # ensures empty_slots never reaches 0, e.g only 1 empty slot
        reserved_for_other_slots += empty_slots * min_cost_by_position.get(pos, 0.0) # need to by at least the cheapest player per pos

    max_price_for_slot = budget_remaining - reserved_for_other_slots

    all_scores = get_all_scores(session)

    candidates = (
        session.query(Player)
        .filter(
            Player.position == position,
            Player.now_cost <= max_price_for_slot,
            Player.id.notin_(other_player_ids),  # can't recommend a player you already own
        )
        .all()
    )

    # drop anyone from a club you're already at the 3-player cap with
    candidates = [club for club in candidates if club_counts.get(club.team_id, 0) < MAX_PER_CLUB]

    def get_score_for(candidate):
        return all_scores.get(candidate.id, 0)

    # best score first, then keep only the top few to show the user a shortlist
    candidates.sort(key=get_score_for, reverse=True)
    top_candidates = candidates[:SLOT_SUGGESTION_COUNT]

    return {
        "suggestions": [
            {"player": c, "score": all_scores.get(c.id, 0)} for c in top_candidates
        ],
        "budget_remaining": round(budget_remaining, 1),
        "max_price_for_slot": round(max_price_for_slot, 1),
    }

