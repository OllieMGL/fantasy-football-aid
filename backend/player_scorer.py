from sqlalchemy.orm import sessionmaker
from db import engine
from models import Player

Session = sessionmaker(bind=engine)
session = Session()

# goalkeeper
# - clean_sheets ~ reward 28%
# - clean_sheets ~ reward 28%
# - total_points ~ reward 20%
# - form ~ reward 18%
# - value (points / cost) ~ reward 12%
# - saves ~ reward 9%
# - goals_conceded ~ punish	9%
# - penalties_saved ~ reward 2%
# - cards ~ punish 2%   ==> keepers rarely get cards so small weighting 

GOALKEEPER_WEIGHTS = {
    "clean_sheets": 0.28,
    "total_points": 0.20,
    "form": 0.18,
    "value": 0.12,
    "saves": 0.09,
    "goals_conceded": 0.09,  # punish
    "penalties_saved": 0.02,
    "cards": 0.02,            # punish
}

def get_goalkeepers(session):
    goalkeepers = (
        session.query(Player)
        .filter(Player.position == "GKP")
        .all()
    )
    return goalkeepers

def calculate_ranges(goalkeepers):

    #Returns a dict of (min, max) tuples for every stat we need to normalize.
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
        "cards": cards_values
    }

#     "clean_sheets": (0, 15), (returns this)
#     "saves": (30, 102)...

    final_ranges = {}

    for stat_name, values in ranges.items():
        minimum = min(values)
        maximum = max(values)
        final_ranges[stat_name] = (minimum, maximum)

    return final_ranges



def normalise(value, min_value, max_value):
    if max_value == min_value:
        return 0.5 # everyone identical - avoid dividing by zero
    return (value - min_value) / (max_value - min_value)



def score_goalkeeper(player, ranges):

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

    #punish stats 1 - x
    normalised_goals_conceded = 1 - normalise(stats.goals_conceded, *ranges["goals_conceded"])
    normalised_cards = 1 - normalise(cards, *ranges["cards"])

    score = (
        GOALKEEPER_WEIGHTS["clean_sheets"] * normalised_clean_sheets
        + GOALKEEPER_WEIGHTS["total_points"] * normalised_total_points
        + GOALKEEPER_WEIGHTS["form"] * normalised_form
        + GOALKEEPER_WEIGHTS["value"] * normalised_value
        + GOALKEEPER_WEIGHTS["saves"] * normalised_saves
        + GOALKEEPER_WEIGHTS["goals_conceded"] * normalised_goals_conceded
        + GOALKEEPER_WEIGHTS["penalties_saved"] * normalised_penalties_saved
        + GOALKEEPER_WEIGHTS["cards"] * normalised_cards
    )

    return round(score * 100, 1)

def score_all_goalkeepers(session):
    goalkeepers = get_goalkeepers(session)
    ranges = calculate_ranges(goalkeepers)

    scores = {}

    for i in goalkeepers:
        player_score = score_goalkeeper(i, ranges)
        scores[i.id] = player_score
    return scores


def goalkeepers_main():
    Session = sessionmaker(bind=engine)
    session = Session()

    goalkeepers = get_goalkeepers(session)
    scores = score_all_goalkeepers(session)

    for p in goalkeepers:
        print(p.first_name, p.second_name, "-", scores[p.id])

goalkeepers_main()