from scorers.goalkeeper_scorer import score_all_goalkeepers, GOALKEEPER_WEIGHTS
from scorers.defender_scorer import score_all_defenders, DEFENDER_WEIGHTS
from scorers.midfielder_scorer import score_all_midfielders, MIDFIELDER_WEIGHTS
from scorers.forward_scorer import score_all_forwards, FORWARD_WEIGHTS
from models import Player

SCORE_FUNCTIONS_BY_POSITION = {
    "GKP": score_all_goalkeepers,
    "DEF": score_all_defenders,
    "MID": score_all_midfielders,
    "FWD": score_all_forwards,
}

WEIGHTS_BY_POSITION = {
    "GKP": GOALKEEPER_WEIGHTS,
    "DEF": DEFENDER_WEIGHTS,
    "MID": MIDFIELDER_WEIGHTS,
    "FWD": FORWARD_WEIGHTS,
}

# Maps a position code to the name of the SQLAlchemy relationship on Player
# that holds that position's stats. Used with getattr() below to pick the
# right stats object for a player without an if/elif per position -
# e.g. "MID" -> "midfielder_stats" -> player.midfielder_stats
STATS_RELATIONSHIP_BY_POSITION = {
    "GKP": "goalkeeper_stats",
    "DEF": "defender_stats",
    "MID": "midfielder_stats",
    "FWD": "forward_stats",
}

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "explain_player_score",
        "description": (
            "Explains why a specific named player has the score they do, using "
            "their real stats and the app's scoring weights for their position. "
            "Use this when the user asks about a specific player by name."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "player_name": {
                    "type": "string",
                    "description": "The player's name, as mentioned by the user (e.g. 'Cole Palmer' or just 'Palmer').",
                },
            },
            "required": ["player_name"],
        },
    },
}


def find_player_by_name(name, session):
    """No fuzzy-matching library here - just an exact full-name match first,
    falling back to a substring match (so 'Palmer' finds 'Cole Palmer'). Not
    perfect if two players share a surname, but honest about what it is."""

    search = name.strip().lower()
    players = session.query(Player).all()

    for player in players:
        full_name = f"{player.first_name} {player.second_name}".lower()
        if full_name == search:
            return player

    for player in players:
        full_name = f"{player.first_name} {player.second_name}".lower()
        if search in full_name:
            return player

    return None


def call_explain_player_score(player_name, player_ids, session):

    player = find_player_by_name(player_name, session)

    if player is None:
        return {"error": f"Couldn't find a player matching '{player_name}'."}

    score_function = SCORE_FUNCTIONS_BY_POSITION[player.position]
    score = score_function(session).get(player.id)

    # pull the raw, position-specific numbers straight off the stats row -
    # everything the scoring algorithm actually sees, without hand-listing
    # them per position - generic across all four stats tables
    stats_object = getattr(player, STATS_RELATIONSHIP_BY_POSITION[player.position]) #
    raw_stats = {
        column.name: getattr(stats_object, column.name)
        for column in stats_object.__table__.columns
        if column.name != "player_id"
    }

    return {
        "name": f"{player.first_name} {player.second_name}",
        "position": player.position,
        "price": player.now_cost,
        "total_points": player.total_points,
        "form": player.form,
        "score": score,
        "raw_stats": raw_stats,
        "scoring_weights_for_position": WEIGHTS_BY_POSITION[player.position],
    }
