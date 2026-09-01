from team_scorer import get_players_by_ids, score_team, check_valid_team

# The description of the function that gets sent to the model - it's metadata,
# not code. The model reads this and decides WHETHER and WHEN to call it; it
# never runs anything itself. "parameters" is empty because the model doesn't
# need to tell us anything here - it doesn't know (and doesn't need to know)
# which players are in the squad. We already know that from the request, so
# we supply player_ids ourselves down in call_get_team_score, not the model.

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_team_score",
        "description": (
            "Calculates the user's current squad's overall score out of 100, "
            "using the app's own weighted scoring algorithm across all 15 players."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


def call_get_team_score(player_ids, session):
    """The real work - runs the app's actual scoring logic against the actual database.
    This is the function TOOL_SCHEMA above is just describing to the model."""

    team_players = get_players_by_ids(player_ids, session)
    errors = check_valid_team(team_players)

    if errors:
        return {"error": " ".join(errors)}

    score = score_team(player_ids, session)
    return {"score": score}
