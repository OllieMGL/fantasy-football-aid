from models import Player
from scorers.common import normalise, get_team_difficulties, normalised_fixture_difficulty_for

# goalkeeper
# - clean_sheets ~ reward 24%
# - total_points ~ reward 18%
# - form ~ reward 16%
# - value (points / cost) ~ reward 12%
# - saves ~ reward 9%
# - goals_conceded ~ punish 9%
# - fixture_difficulty ~ punish 8%
# - penalties_saved ~ reward 2%
# - cards ~ punish 2%

GOALKEEPER_WEIGHTS = {
    "clean_sheets": 0.24,
    "total_points": 0.18,
    "form": 0.16,
    "value": 0.12,
    "saves": 0.09,
    "goals_conceded": 0.09,       # punish
    "fixture_difficulty": 0.08,    # punish
    "penalties_saved": 0.02,
    "cards": 0.02,                  # punish
}


def get_goalkeepers(session):
    goalkeepers = (
        session.query(Player)
        .filter(Player.position == "GKP")
        .all()
    )
    return goalkeepers


def calculate_ranges(goalkeepers, session):
    # Returns a dict of (min, max) tuples for every stat we need to normalise 
    # Returns teams difficulties

    team_difficulties = get_team_difficulties(goalkeepers, session)

    fixture_difficulty_values = [
        team_difficulties[p.team_id] for p in goalkeepers
        if team_difficulties[p.team_id] is not None
    ]

    cards_values = [
        p.goalkeeper_stats.yellow_cards + (p.goalkeeper_stats.red_cards * 3)
        for p in goalkeepers
    ]
    value_values = [p.total_points / p.now_cost for p in goalkeepers]

    ranges = {
        "clean_sheets": [p.goalkeeper_stats.clean_sheets for p in goalkeepers],
        "saves": [p.goalkeeper_stats.saves for p in goalkeepers],
        "goals_conceded": [p.goalkeeper_stats.goals_conceded for p in goalkeepers],
        "penalties_saved": [p.goalkeeper_stats.penalties_saved for p in goalkeepers],
        "total_points": [p.total_points for p in goalkeepers],
        "form": [p.form for p in goalkeepers],
        "value": value_values,
        "cards": cards_values,
        "fixture_difficulty": fixture_difficulty_values,
    }

    #     "clean_sheets": (0, 15), (returns this)
    #     "saves": (30, 102)...

    final_ranges = {}

    for stat_name, values in ranges.items():
        minimum = min(values)
        maximum = max(values)
        final_ranges[stat_name] = (minimum, maximum)

    return final_ranges, team_difficulties


def score_goalkeeper(player, ranges, team_difficulties):
    stats = player.goalkeeper_stats
    cards = stats.yellow_cards + (stats.red_cards * 3)
    value = player.total_points / player.now_cost

    # the  * unpacks the min max values from ranges sos it can be readily used
    # same thing as: normalise(value, range["value"][0], range["value"][1])

    normalised_clean_sheets = normalise(stats.clean_sheets, *ranges["clean_sheets"])
    normalised_total_points = normalise(player.total_points, *ranges["total_points"])
    normalised_form = normalise(player.form, *ranges["form"])
    normalised_value = normalise(value, *ranges["value"])
    normalised_saves = normalise(stats.saves, *ranges["saves"])
    normalised_penalties_saved = normalise(stats.penalties_saved, *ranges["penalties_saved"])

    # punish stats: 1 - x
    normalised_goals_conceded = 1 - normalise(stats.goals_conceded, *ranges["goals_conceded"])
    normalised_cards = 1 - normalise(cards, *ranges["cards"])

    normalised_fixture_difficulty = normalised_fixture_difficulty_for(player, ranges, team_difficulties)

    score = (
        GOALKEEPER_WEIGHTS["clean_sheets"] * normalised_clean_sheets
        + GOALKEEPER_WEIGHTS["total_points"] * normalised_total_points
        + GOALKEEPER_WEIGHTS["form"] * normalised_form
        + GOALKEEPER_WEIGHTS["value"] * normalised_value
        + GOALKEEPER_WEIGHTS["saves"] * normalised_saves
        + GOALKEEPER_WEIGHTS["goals_conceded"] * normalised_goals_conceded
        + GOALKEEPER_WEIGHTS["penalties_saved"] * normalised_penalties_saved
        + GOALKEEPER_WEIGHTS["cards"] * normalised_cards
        + GOALKEEPER_WEIGHTS["fixture_difficulty"] * normalised_fixture_difficulty
    )

    return round(score * 100, 1)


def score_all_goalkeepers(session):
    goalkeepers = get_goalkeepers(session)
    ranges, team_difficulties = calculate_ranges(goalkeepers, session)

    scores = {}

    for p in goalkeepers:
        player_score = score_goalkeeper(p, ranges, team_difficulties)
        scores[p.id] = player_score

    return scores