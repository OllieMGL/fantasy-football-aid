from team_scorer import get_players_by_ids, score_team, check_valid_team


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


# budget not needed but needs to be passed 
def call_get_team_score(player_ids, session, budget):
    """The real work - runs the app's actual scoring logic against the actual database.
    This is the function TOOL_SCHEMA above is just describing to the model."""

    team_players = get_players_by_ids(player_ids, session)
    errors = check_valid_team(team_players)

    if errors:
        return {"error": " ".join(errors)}

    score = score_team(player_ids, session)
    return {"score": score}
