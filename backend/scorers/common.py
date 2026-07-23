from sqlalchemy import or_
from models import Fixture


def normalise(value, min_value, max_value):
    if max_value == min_value:
        return 0.5  # everyone identical - avoid dividing by zero
    return (value - min_value) / (max_value - min_value)


def get_fixture_difficulty(team_id, session):
    upcoming_fixtures = (
        session.query(Fixture)
        .filter(
            or_(Fixture.home_team == team_id, Fixture.away_team == team_id),
            Fixture.finished == False,
        )
        .order_by(Fixture.gameweek)
        .limit(5)  # looks at the next five gameweeks
        .all()
    )

    if not upcoming_fixtures:
        return None  # no upcoming fixtures found for this team

    difficulties = []

    for fixture in upcoming_fixtures:
        if fixture.home_team == team_id:
            difficulties.append(fixture.team_h_difficulty)
        else:
            difficulties.append(fixture.team_a_difficulty)

    average_difficulty = sum(difficulties) / len(difficulties)
    return average_difficulty


# returns dictionary of teamID ==> average fixture difficulty calculated
# once per team rather than once per player
def get_team_difficulties(players, session):

    unique_team_ids = {p.team_id for p in players}
    team_difficulties = {}

    for team_id in unique_team_ids:
        difficulty = get_fixture_difficulty(team_id, session)
        team_difficulties[team_id] = difficulty

    return team_difficulties


# looks up team's fixture difficulty 
def normalised_fixture_difficulty_for(player, ranges, team_difficulties):

    fixture_difficulty = team_difficulties.get(player.team_id)

    return 1 - normalise(fixture_difficulty, *ranges["fixture_difficulty"])