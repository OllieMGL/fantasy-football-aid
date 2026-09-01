from recommend_player import recommend_for_slot, get_all_scores, find_weakest_by_position, REQUIRED_COUNTS
from team_scorer import get_players_by_ids

# The description of the function that gets sent to the model - it's metadata,
# not code. Unlike get_team_score, this one has a real argument: the model has
# to read the user's question and decide which position they mean.

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "recommend_for_slot",
        "description": (
            "Suggests players to bring into a specific position, ranked by the app's "
            "scoring algorithm, that fit within the budget left after the user's current squad."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "position": {
                    "type": "string",
                    "enum": ["GKP", "DEF", "MID", "FWD"], # limits the AI to these choices - needed in this format for algorithm 
                    "description": "The position to find a player for.",
                },
            },
            "required": ["position"],
        },
    },
}


def call_recommend_for_slot(position, player_ids, session):

    # if that position is already full, "who should I bring in for X" really means
    # "who should replace my weakest X" - so free up that one player's slot and
    # cost first, same as clicking an already-filled slot in the picker would.
    # if the position isn't full, there's a genuine empty slot already and no one
    # needs excluding - recommend_for_slot handles that case fine on its own.
    team_players = get_players_by_ids(player_ids, session)
    position_count = sum(1 for p in team_players if p.position == position)

    if position_count >= REQUIRED_COUNTS[position]:
        all_scores = get_all_scores(session)
        weakest = find_weakest_by_position(team_players, all_scores).get(position)
        if weakest:
            player_ids = [pid for pid in player_ids if pid != weakest.id]

    # has to change the SQL Alchemy player objects into plain dicts
    # as only plain data can be sent back to the model as JSON

    result = recommend_for_slot(position, player_ids, session)

    return {
        "suggestions": [
            {
                "name": f"{s['player'].first_name} {s['player'].second_name}",
                "price": s["player"].now_cost,
                "score": s["score"],
            }
            for s in result["suggestions"]
        ],
        "budget_remaining": result["budget_remaining"],
        "max_price_for_slot": result["max_price_for_slot"],
    }
