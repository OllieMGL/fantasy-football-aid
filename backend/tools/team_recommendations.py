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
            "Covers all four positions at once. Each position comes back with an "
            "'action': 'fill' means the squad is short there, so the suggestions "
            "listed are players to ADD; 'upgrade' means it's already full, so it "
            "gives the weakest current player and a similarly-priced replacement "
            "that scores higher (or null if nothing better exists). Also reports "
            "filled/required/missing counts per position."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def call_get_recommendations(player_ids, session):
    """The real work - runs the app's actual recommendation logic, then swaps the
    SQLAlchemy Player objects for plain names/prices the model can read."""

    recommendations = get_recommendations(player_ids, session)

    result = {}
    for position, info in recommendations.items():
        entry = {
            "action": info["action"],
            "filled": info["filled"],
            "required": info["required"],
            "missing": info["missing"],
        }

        if info["action"] == "fill":
            entry["suggestions"] = [
                {
                    "name": f"{s['player'].first_name} {s['player'].second_name}",
                    "price": s["player"].now_cost,
                    "score": s["score"],
                }
                for s in info["suggestions"]
            ]
        else:
            current = info["current_player"]
            replacement = info["suggested_replacement"]

            entry["current_player"] = f"{current.first_name} {current.second_name}"
            entry["current_price"] = current.now_cost
            entry["current_score"] = info["current_score"]
            entry["suggested_replacement"] = (
                f"{replacement.first_name} {replacement.second_name}" if replacement else None
            )
            entry["suggested_price"] = replacement.now_cost if replacement else None
            entry["suggested_score"] = info["suggested_score"]

        result[position] = entry

    return result
