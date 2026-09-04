from recommend_player import get_recommendations, REQUIRED_COUNTS
from team_scorer import get_players_by_ids

# Empty parameters again, but for a different reason than get_team_score's:
# this tool deliberately covers every position at once - "where are my weak
# spots" is a whole-squad question, so there's no single argument for the
# model to narrow it down to.

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_recommendations",
        "description": (
            "Reports two things about the user's whole squad: (1) squad_completeness - "
            "how many players are currently filled vs required in each position, so you "
            "can see which positions are empty or short; (2) weak_player_swap_suggestions - "
            "for positions that already have a player, the weakest one and a similarly-priced "
            "replacement if one scores higher. Only use the swap suggestions for positions "
            "that are actually filled - for empty or under-filled positions, use "
            "recommend_for_slot instead."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def call_get_recommendations(player_ids, session):
    """The real work - finds the weakest player in each position and a possible
    upgrade for each, using the app's actual scoring algorithm and database."""

    recommendations = get_recommendations(player_ids, session)

    swap_suggestions = {}
    for position, info in recommendations.items():
        current = info["current_player"]
        replacement = info["suggested_replacement"]

        swap_suggestions[position] = {
            "current_player": f"{current.first_name} {current.second_name}",
            "current_price": current.now_cost,
            "current_score": info["current_score"],
            "suggested_replacement": (
                f"{replacement.first_name} {replacement.second_name}" if replacement else None
            ),
            "suggested_price": replacement.now_cost if replacement else None,
            "suggested_score": info["suggested_score"],
        }

    # get_recommendations() above only ever reports on positions the user
    # already has at least one player in - it has no visibility into empty
    # positions at all. Add that separately, so the model can tell "needs
    # filling from scratch" apart from "already there, could be upgraded".
    team_players = get_players_by_ids(player_ids, session)
    filled_counts = {position: 0 for position in REQUIRED_COUNTS}
    for player in team_players:
        filled_counts[player.position] += 1

    squad_completeness = {
        position: {"filled": filled_counts[position], "required": required}
        for position, required in REQUIRED_COUNTS.items()
    }

    return {
        "squad_completeness": squad_completeness,
        "weak_player_swap_suggestions": swap_suggestions,
    }
