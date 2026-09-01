from recommend_player import get_recommendations

# Empty parameters again, but for a different reason than get_team_score's:
# this tool deliberately covers every position at once - "where are my weak
# spots" is a whole-squad question, so there's no single argument for the
# model to narrow it down to.

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_recommendations",
        "description": (
            "Finds the weakest player in each position across the user's whole "
            "squad, and suggests a similarly-priced replacement if one scores "
            "higher on the app's algorithm. Covers all positions at once."
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

    result = {}
    for position, info in recommendations.items():
        current = info["current_player"]
        replacement = info["suggested_replacement"]

        result[position] = {
            "current_player": f"{current.first_name} {current.second_name}",
            "current_price": current.now_cost,
            "current_score": info["current_score"],
            "suggested_replacement": (
                f"{replacement.first_name} {replacement.second_name}" if replacement else None
            ),
            "suggested_price": replacement.now_cost if replacement else None,
            "suggested_score": info["suggested_score"],
        }

    return result
