from sqlalchemy import func
from scorers.goalkeeper_scorer import score_all_goalkeepers
from scorers.defender_scorer import score_all_defenders
from scorers.midfielder_scorer import score_all_midfielders
from scorers.forward_scorer import score_all_forwards
from team_scorer import get_players_by_ids
from models import Player

REQUIRED_COUNTS = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}

# the budget for a squad built by hand. An imported squad's budget is its value
# plus the bank instead - the frontend works that out and sends it in
BUDGET_LIMIT = 100.0
MAX_PER_CLUB = 3
SLOT_SUGGESTION_COUNT = 4

# how many suggestions
OVERVIEW_SUGGESTION_COUNT = 2

# an upgrade suggestion is a player within £0.5m of the one being replaced
REPLACEMENT_PRICE_WINDOW = 0.5


def get_squad_completeness(players):
    # {"GKP": {"filled": 2, "required": 2, "missing": 0}, ...}

    filled_counts = {position: 0 for position in REQUIRED_COUNTS}
    for player in players:
        filled_counts[player.position] += 1

    return {
        position: {
            "filled": filled_counts[position],
            "required": required,
            # max(0, ...) so an over-filled position reads 0, never negative
            "missing": max(0, required - filled_counts[position]),
        }
        for position, required in REQUIRED_COUNTS.items()
    }


def count_by_club(players):
    # {team_id: how many players from that club} - used to enforce the max 3
    # players from any one real team
    club_counts = {}

    for player in players:
        club_counts[player.team_id] = club_counts.get(player.team_id, 0) + 1

    return club_counts


def get_all_scores(session):
    # every player in the league, scored - {player_id: score}
    all_scores = {}

    all_scores.update(score_all_goalkeepers(session))
    all_scores.update(score_all_defenders(session))
    all_scores.update(score_all_midfielders(session))
    all_scores.update(score_all_forwards(session))

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

def find_replacement(weak_player, session, all_scores, current_team_ids, club_counts, money_left=None):

    min_price = weak_player.now_cost - REPLACEMENT_PRICE_WINDOW
    max_price = weak_player.now_cost + REPLACEMENT_PRICE_WINDOW

    # selling the weak player gives their price back
    if money_left is not None:
        most_we_can_afford = weak_player.now_cost + money_left

        if most_we_can_afford < max_price:
            max_price = most_we_can_afford

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

    # player dropped frees up a slot for their club
    club_counts_after_drop = dict(club_counts)
    club_counts_after_drop[weak_player.team_id] -= 1

    candidates = [
        candidate for candidate in candidates
        if club_counts_after_drop.get(candidate.team_id, 0) < MAX_PER_CLUB
    ]

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

# Returns (budget_remaining, max_price)
def get_max_price_for_slot(position, other_players, other_player_ids, session, budget=BUDGET_LIMIT):

    amount_spent = sum(player.now_cost for player in other_players)

    # can go negative if a hand-built squad is over £100m - then nothing is
    # affordable, which is correct
    budget_remaining = budget - amount_spent

    completeness = get_squad_completeness(other_players)
    min_cost_by_position = get_min_available_cost_by_position(other_player_ids, session)

    # money that has to stay back for the squad's OTHER empty slots
    reserved_for_other_slots = 0.0
    for pos, counts in completeness.items():
        empty_slots = counts["missing"]

        if pos == position:
            empty_slots -= 1  # this slot is the one being spent on, so don't reserve for it

        empty_slots = max(0, empty_slots)
        reserved_for_other_slots += empty_slots * min_cost_by_position.get(pos, 0.0) # at least the cheapest player per position

    return budget_remaining, budget_remaining - reserved_for_other_slots



def recommend_for_slot(position, other_player_ids, session, all_scores=None, budget=BUDGET_LIMIT):

    other_players = get_players_by_ids(other_player_ids, session)
    club_counts = count_by_club(other_players)

    budget_remaining, max_price_for_slot = get_max_price_for_slot(
        position, other_players, other_player_ids, session, budget=budget
    )

    if all_scores is None:
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
    candidates = [
        candidate for candidate in candidates
        if club_counts.get(candidate.team_id, 0) < MAX_PER_CLUB
    ]

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



# everything feeds into this function 
def get_recommendations(selected_player_ids, session, all_scores=None, budget=BUDGET_LIMIT):

    # One entry per position, "action" says which kind it is:
    #   "fill"    - short of players, so suggest who to ADD
    #   "upgrade" - already full, so suggest a better player for the weakest one

    team_players = get_players_by_ids(selected_player_ids, session)

    # scored once here, then passed down
    if all_scores is None:
        all_scores = get_all_scores(session)

    completeness = get_squad_completeness(team_players)
    club_counts = count_by_club(team_players)
    weakest_by_position = find_weakest_by_position(team_players, all_scores)

    squad_cost = sum(player.now_cost for player in team_players)
    money_left = budget - squad_cost

    recommendations = {}
    # recommendations creates a nested dictionary
    # Key is position and the value is another dictionary containing the infomation below

    for position, counts in completeness.items():

        if counts["missing"] > 0:
            slot = recommend_for_slot(
                position, selected_player_ids, session, all_scores=all_scores, budget=budget
            )

            recommendations[position] = {
                "action": "fill",
                **counts,
                "max_price_for_slot": slot["max_price_for_slot"],
                "suggestions": slot["suggestions"][:OVERVIEW_SUGGESTION_COUNT],
            }

        else:
            # filled means at least one player, so weakest_by_position always has this one
            weak_player = weakest_by_position[position]
            replacement = find_replacement(
                weak_player, session, all_scores, selected_player_ids, club_counts,
                money_left=money_left,
            )

            recommendations[position] = {
                "action": "upgrade",
                **counts,
                "current_player": weak_player,
                "current_score": all_scores[weak_player.id],
                "suggested_replacement": replacement,
                "suggested_score": all_scores[replacement.id] if replacement else None,
            }

    return recommendations

