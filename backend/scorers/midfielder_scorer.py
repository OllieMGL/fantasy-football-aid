from models import Player
from scorers.common import normalise

# midfielder
# - total_points ~ reward 20%
# - goals_scored ~ reward 18%
# - form ~ reward 14%
# - value (points / cost) ~ reward 12%
# - assists ~ reward 11%
# - expected_goals + expected_assists (combined) ~ reward 10%
# - clean_sheets ~ reward 6%
# - creativity ~ reward 4%
# - cards ~ punish 5%

MIDFIELDER_WEIGHTS = {
    "total_points": 0.20,
    "goals_scored": 0.18,
    "form": 0.14,
    "value": 0.12,
    "assists": 0.11,
    "expected_returns": 0.10,  # expected_goals + expected_assists, combined
    "clean_sheets": 0.06,
    "creativity": 0.04,
    "cards": 0.05      # punish
}

def get_midfielders(session):
    midfielders = (
        session.query(Player)
        .filter(Player.position == "MID")
        .all()
    )
    return midfielders


def calculate_ranges(midfielders):

    expected_returns_values = [
        p.midfielder_stats.expected_goals + p.midfielder_stats.expected_assists
        for p in midfielders
    ]
    cards_values = [
        p.midfielder_stats.yellow_cards + (p.midfielder_stats.red_cards * 3)
        for p in midfielders
    ]
    value_values = [p.total_points / p.now_cost for p in midfielders]

    ranges = {
        "total_points": [p.total_points for p in midfielders],
        "goals_scored": [p.midfielder_stats.goals_scored for p in midfielders],
        "form": [p.form for p in midfielders],
        "value": value_values,
        "assists": [p.midfielder_stats.assists for p in midfielders],
        "expected_returns": expected_returns_values,
        "clean_sheets": [p.midfielder_stats.clean_sheets for p in midfielders],
        "creativity": [p.midfielder_stats.creativity for p in midfielders],
        "cards": cards_values,
    }

    final_ranges = {}

    for stat_name, values in ranges.items():
        minimum = min(values)
        maximum = max(values)
        final_ranges[stat_name] = (minimum, maximum)

    return final_ranges


def score_midfielder(player, ranges):
    stats = player.midfielder_stats
    expected_returns = stats.expected_goals + stats.expected_assists
    cards = stats.yellow_cards + (stats.red_cards * 3)
    value = player.total_points / player.now_cost

    normalised_total_points = normalise(player.total_points, *ranges["total_points"])
    normalised_goals_scored = normalise(stats.goals_scored, *ranges["goals_scored"])
    normalised_form = normalise(player.form, *ranges["form"])
    normalised_value = normalise(value, *ranges["value"])
    normalised_assists = normalise(stats.assists, *ranges["assists"])
    normalised_expected_returns = normalise(expected_returns, *ranges["expected_returns"])
    normalised_clean_sheets = normalise(stats.clean_sheets, *ranges["clean_sheets"])
    normalised_creativity = normalise(stats.creativity, *ranges["creativity"])

    # punish stats: 1 - x
    normalised_cards = 1 - normalise(cards, *ranges["cards"])

    score = (
        MIDFIELDER_WEIGHTS["total_points"] * normalised_total_points
        + MIDFIELDER_WEIGHTS["goals_scored"] * normalised_goals_scored
        + MIDFIELDER_WEIGHTS["form"] * normalised_form
        + MIDFIELDER_WEIGHTS["value"] * normalised_value
        + MIDFIELDER_WEIGHTS["assists"] * normalised_assists
        + MIDFIELDER_WEIGHTS["expected_returns"] * normalised_expected_returns
        + MIDFIELDER_WEIGHTS["clean_sheets"] * normalised_clean_sheets
        + MIDFIELDER_WEIGHTS["creativity"] * normalised_creativity
        + MIDFIELDER_WEIGHTS["cards"] * normalised_cards
    )

    return round(score * 100, 1)

def score_all_midfielders(session):
    midfielders = get_midfielders(session)
    ranges = calculate_ranges(midfielders)

    scores = {}

    for p in midfielders:
        player_score = score_midfielder(p, ranges)
        scores[p.id] = player_score

    return scores