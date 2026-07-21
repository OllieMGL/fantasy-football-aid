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

goalkeepers = (
    session.query(Player)
    .filter(Player.position == "GKP")
    .all()
)

# creating a python list for each stat from every goalkeeper
clean_sheets_values = [p.goalkeeper_stats.clean_sheets for p in goalkeepers]
saves_values = [p.goalkeeper_stats.saves for p in goalkeepers]
goals_conceded_values = [p.goalkeeper_stats.goals_conceded for p in goalkeepers]
penalties_saved_values = [p.goalkeeper_stats.penalties_saved for p in goalkeepers]
total_points_values = [p.total_points for p in goalkeepers]
form_values = [p.form for p in goalkeepers]
# cards handled in one for simplcity, red card * 3 as is worse than yellow 
cards_values = [
    p.goalkeeper_stats.yellow_cards + (p.goalkeeper_stats.red_cards * 3)
    for p in goalkeepers
]
# need to calculate the "value"
value_values = [
    p.total_points / p.now_cost for p in goalkeepers
]

def normalise(value, min_value, max_value):
    if max_value == min_value:
        return 0.5 # everyone identical - avoid dividing by zero
    return (value - min_value) / (max_value - min_value)

goalkeeper_scores = {}

for i in goalkeepers:
    stats = i.goalkeeper_stats

    cards = stats.yellow_cards + (stats.red_cards * 3)
    value = i.total_points / i.now_cost

    normalised_clean_sheets = normalise(stats.clean_sheets, min(clean_sheets_values), max(clean_sheets_values))
    normalised_total_points = normalise(i.total_points, min(total_points_values), max(total_points_values))
    normalised_form = normalise(i.form, min(form_values), max(form_values))
    normalised_value = normalise(value, min(value_values), max(value_values))
    normalised_saves = normalise(stats.saves, min(saves_values), max(saves_values))
    normalised_penalties_saved = normalise(stats.penalties_saved, min(penalties_saved_values), max(penalties_saved_values))

    # punish stats ==> 1 - x
    normalised_goals_conceded = 1 - normalise(stats.goals_conceded, min(goals_conceded_values), max(goals_conceded_values))
    normalised_cards = 1 - normalise(cards, min(cards_values), max(cards_values))

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

    goalkeeper_scores[i.id] = round(score * 100, 1)

# Sort and print the top 5, to sanity check the results

top_5 = sorted(goalkeeper_scores.items(), key=lambda item: item[1], reverse=True)[:5]

for player_id, score in top_5:
    player = next(p for p in goalkeepers if p.id == player_id)
    print(player.first_name, player.second_name, "-", score)
