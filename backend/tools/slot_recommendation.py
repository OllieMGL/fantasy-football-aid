from recommend_player import recommend_for_slot, get_all_scores, find_weakest_by_position, REQUIRED_COUNTS
from team_scorer import get_players_by_ids

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


def call_recommend_for_slot(position, player_ids, session, budget):

    team_players = get_players_by_ids(player_ids, session)
    position_count = sum(1 for p in team_players if p.position == position)

    if position_count >= REQUIRED_COUNTS[position]:
        all_scores = get_all_scores(session)
        weakest = find_weakest_by_position(team_players, all_scores).get(position)
        if weakest:
            player_ids = [pid for pid in player_ids if pid != weakest.id]

    result = recommend_for_slot(position, player_ids, session, budget=budget)

    return {
        "suggestions": [
            {
                "id": s["player"].id,
                "name": f"{s['player'].first_name} {s['player'].second_name}",
                "price": s["player"].now_cost,
                "score": s["score"],
            }
            for s in result["suggestions"]
        ],
        "budget_remaining": result["budget_remaining"],
        "max_price_for_slot": result["max_price_for_slot"],
    }
