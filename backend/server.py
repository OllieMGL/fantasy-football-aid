from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import sessionmaker

from db import engine
from models import Player
from team_scorer import get_players_by_ids, score_team, check_valid_team
from recommend_player import get_recommendations
from import_team import import_team


app = Flask(__name__)
CORS(app)
Session = sessionmaker(bind=engine)


def create_player(player):
    if player is None:
        return None

    return {
        "id": player.id,
        "first_name": player.first_name,
        "second_name": player.second_name,
        "position": player.position,
        "now_cost": player.now_cost,
        "total_points": player.total_points,
    }


@app.route("/players", methods=["GET"])
def list_players():
    session = Session()

    players = session.query(Player).all()
    result = [create_player(player) for player in players]

    session.close()
    return jsonify(result)


@app.route("/score-team", methods=["POST"])
def score_team_endpoint():

    data = request.get_json()
    player_ids = data.get("player_ids")

    if not player_ids:
        return jsonify({"error": "player_ids is required"}), 400

    session = Session()

    team_players = get_players_by_ids(player_ids, session)
    errors = check_valid_team(team_players)

    if errors:
        session.close()
        return jsonify({"errors": errors}), 400

    score = score_team(player_ids, session)

    session.close()
    return jsonify({"score": score})


@app.route("/recommendations", methods=["POST"])
def recommendations_endpoint():
    data = request.get_json()
    player_ids = data.get("player_ids")

    if not player_ids:
        return jsonify({"error": "player_ids is required"}), 400

    session = Session()

    team_players = get_players_by_ids(player_ids, session)
    errors = check_valid_team(team_players)
    if errors:
        session.close()
        return jsonify({"errors": errors}), 400

    recommendations = get_recommendations(player_ids, session)

    result = {
        position: {
            "current_player": create_player(info["current_player"]),
            "current_score": info["current_score"],
            "suggested_replacement": create_player(info["suggested_replacement"]),
            "suggested_score": info["suggested_score"],
        }
        for position, info in recommendations.items()
    }

    session.close()
    return jsonify(result)

    
@app.route("/import-team/<int:team_id>", methods=["GET"])
def import_team_endpoint(team_id):
    result = import_team(team_id)

    if result is None:
        return jsonify({"error": f"Could not find FPL team with id {team_id}"}), 404

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)