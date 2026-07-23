from models import Player
from scorers.common import normalise, get_team_difficulties, normalised_fixture_difficulty_for

# defender
# - clean_sheets ~ reward 22%
# - total_points ~ reward 17%
# - form ~ reward 14%
# - expected_goals_conceded ~ punish 12%
# - goals_scored + assists (combined) ~ reward 12%
# - fixture_difficulty ~ punish 8%
# - value (points / cost) ~ reward 7%
# - cards ~ punish 5%
# - goals_conceded ~ punish 2%
# - own_goals ~ punish 1%

DEFENDER_WEIGHTS = {
    "clean_sheets": 0.22,
    "total_points": 0.17,
    "form": 0.14,
    "expected_goals_conceded": 0.12,  # punish
    "attacking_returns": 0.12,
    "fixture_difficulty": 0.08,        # punish
    "value": 0.07,
    "cards": 0.05,                       # punish
    "goals_conceded": 0.02,               # punish
    "own_goals": 0.01,                     # punish
}

def get_defenders(session):
    defenders=(
        session.query(Player)
        .filter(Player.position == "DEF")
        .all()
    )
    return defenders


def calculate_ranges(defenders, session):

    team_difficulties = get_team_difficulties(defenders, session)

    fixture_difficulty_values = [
        team_difficulties[p.team_id] for p in defenders
        if team_difficulties[p.team_id] is not None
    ]

    attacking_returns_values = [
        p.defender_stats.goals_scored + p.defender_stats.assists
        for p in defenders
    ]
    cards_values = [
        p.defender_stats.yellow_cards + (p.defender_stats.red_cards * 3)
        for p in defenders
    ]

    value_values = [p.total_points / p.now_cost for p in defenders]

    ranges = {
        "clean_sheets": [p.defender_stats.clean_sheets for p in defenders],
        "total_points": [p.total_points for p in defenders],
        "form": [p.form for p in defenders],
        "expected_goals_conceded": [p.defender_stats.expected_goals_conceded for p in defenders],
        "attacking_returns": attacking_returns_values,
        "value": value_values,
        "goals_conceded": [p.defender_stats.goals_conceded for p in defenders],
        "own_goals": [p.defender_stats.own_goals for p in defenders],
        "cards": cards_values,
        "fixture_difficulty": fixture_difficulty_values,
    }

    final_ranges = {}

    #.items returns this 
#     [
#     ("clean_sheets", [4, 9, 2, 12]),
#     ("total_points", [88, 145, 60, 130]),
#     ("cards", [3, 7, 1, 5])...
#      ]
    for stat_name, values in ranges.items():
        minimum = min(values)
        maximum = max(values)
        final_ranges[stat_name] = (minimum, maximum)

    return final_ranges, team_difficulties

def score_defender(player, ranges, team_difficulties):

    stats = player.defender_stats
    attacking_returns = stats.goals_scored + stats.assists
    cards = stats.yellow_cards + (stats.red_cards * 3)
    value = player.total_points / player.now_cost

    normalised_clean_sheets = normalise(stats.clean_sheets, *ranges["clean_sheets"])
    normalised_total_points = normalise(player.total_points, *ranges["total_points"])
    normalised_form = normalise(player.form, *ranges["form"])
    normalised_attacking_returns = normalise(attacking_returns, *ranges["attacking_returns"])
    normalised_value = normalise(value, *ranges["value"])

    # punish stats: 1 - x
    normalised_expected_goals_conceded = 1 - normalise(stats.expected_goals_conceded, *ranges["expected_goals_conceded"])
    normalised_goals_conceded = 1 - normalise(stats.goals_conceded, *ranges["goals_conceded"])
    normalised_own_goals = 1 - normalise(stats.own_goals, *ranges["own_goals"])
    normalised_cards = 1 - normalise(cards, *ranges["cards"])

    normalised_fixture_difficulty = normalised_fixture_difficulty_for(player, ranges, team_difficulties)

    score = (
        DEFENDER_WEIGHTS["clean_sheets"] * normalised_clean_sheets
        + DEFENDER_WEIGHTS["total_points"] * normalised_total_points
        + DEFENDER_WEIGHTS["form"] * normalised_form
        + DEFENDER_WEIGHTS["expected_goals_conceded"] * normalised_expected_goals_conceded
        + DEFENDER_WEIGHTS["attacking_returns"] * normalised_attacking_returns
        + DEFENDER_WEIGHTS["value"] * normalised_value
        + DEFENDER_WEIGHTS["goals_conceded"] * normalised_goals_conceded
        + DEFENDER_WEIGHTS["own_goals"] * normalised_own_goals
        + DEFENDER_WEIGHTS["cards"] * normalised_cards
        + DEFENDER_WEIGHTS["fixture_difficulty"] * normalised_fixture_difficulty
    )

    return round(score * 100, 1) 


def score_all_defenders(session):

    defenders = get_defenders(session)
    ranges, team_difficulties = calculate_ranges(defenders, session)

    scores = {}

    for p in defenders:
        player_score = score_defender(p, ranges, team_difficulties)
        scores[p.id] = player_score

    return scores