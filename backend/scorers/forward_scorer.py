from models import Player
from scorers.common import normalise

# forward
# - goals_scored ~ reward 25%
# - total_points ~ reward 18%
# - form ~ reward 14%
# - expected_goals ~ reward 12%
# - assists ~ reward 10%
# - value (points / cost) ~ reward 10%
# - threat ~ reward 6%
# - penalties_missed ~ punish 3%
# - cards ~ punish 2%

FORWARD_WEIGHTS = {
    "goals_scored": 0.25,
    "total_points": 0.18,
    "form": 0.14,
    "expected_goals": 0.12,
    "assists": 0.10,
    "value": 0.10,
    "threat": 0.06,
    "penalties_missed": 0.03,  # punish
    "cards": 0.02,              # punish
}

from models import Player
from scorers.common import normalise

# forward
# - goals_scored ~ reward 25%
# - total_points ~ reward 18%
# - form ~ reward 14%
# - expected_goals ~ reward 12%
# - assists ~ reward 10%
# - value (points / cost) ~ reward 10%
# - threat ~ reward 6%
# - penalties_missed ~ punish 3%
# - cards ~ punish 2%

FORWARD_WEIGHTS = {
    "goals_scored": 0.25,
    "total_points": 0.18,
    "form": 0.14,
    "expected_goals": 0.12,
    "assists": 0.10,
    "value": 0.10,
    "threat": 0.06,
    "penalties_missed": 0.03,  # punish
    "cards": 0.02,              # punish
}


def get_forwards(session):
    forwards = (
        session.query(Player)
        .filter(Player.position == "FWD")
        .all()
    )
    return forwards


def calculate_ranges(forwards):
    cards_values = [
        p.forward_stats.yellow_cards + (p.forward_stats.red_cards * 3)
        for p in forwards
    ]
    value_values = [p.total_points / p.now_cost for p in forwards]

    ranges = {
        "goals_scored": [p.forward_stats.goals_scored for p in forwards],
        "total_points": [p.total_points for p in forwards],
        "form": [p.form for p in forwards],
        "expected_goals": [p.forward_stats.expected_goals for p in forwards],
        "assists": [p.forward_stats.assists for p in forwards],
        "value": value_values,
        "threat": [p.forward_stats.threat for p in forwards],
        "penalties_missed": [p.forward_stats.penalties_missed for p in forwards],
        "cards": cards_values,
    }

    final_ranges = {}

    for stat_name, values in ranges.items():
        minimum = min(values)
        maximum = max(values)
        final_ranges[stat_name] = (minimum, maximum)

    return final_ranges


def score_forward(player, ranges):
    stats = player.forward_stats
    cards = stats.yellow_cards + (stats.red_cards * 3)
    value = player.total_points / player.now_cost

    normalised_goals_scored = normalise(stats.goals_scored, *ranges["goals_scored"])
    normalised_total_points = normalise(player.total_points, *ranges["total_points"])
    normalised_form = normalise(player.form, *ranges["form"])
    normalised_expected_goals = normalise(stats.expected_goals, *ranges["expected_goals"])
    normalised_assists = normalise(stats.assists, *ranges["assists"])
    normalised_value = normalise(value, *ranges["value"])
    normalised_threat = normalise(stats.threat, *ranges["threat"])

    # punish stats: 1 - x
    normalised_penalties_missed = 1 - normalise(stats.penalties_missed, *ranges["penalties_missed"])
    normalised_cards = 1 - normalise(cards, *ranges["cards"])

    score = (
        FORWARD_WEIGHTS["goals_scored"] * normalised_goals_scored
        + FORWARD_WEIGHTS["total_points"] * normalised_total_points
        + FORWARD_WEIGHTS["form"] * normalised_form
        + FORWARD_WEIGHTS["expected_goals"] * normalised_expected_goals
        + FORWARD_WEIGHTS["assists"] * normalised_assists
        + FORWARD_WEIGHTS["value"] * normalised_value
        + FORWARD_WEIGHTS["threat"] * normalised_threat
        + FORWARD_WEIGHTS["penalties_missed"] * normalised_penalties_missed
        + FORWARD_WEIGHTS["cards"] * normalised_cards
    )

    return round(score * 100, 1)


def score_all_forwards(session):
    forwards = get_forwards(session)
    ranges = calculate_ranges(forwards)

    scores = {}

    for p in forwards:
        player_score = score_forward(p, ranges)
        scores[p.id] = player_score

    return scores