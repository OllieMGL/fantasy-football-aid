from get_data import get_entry_data, get_entry_picks

# two custom errors - used for when it is a false team ID 
# and when the gameweek number gets an errror - eg season has not started yet

class TeamNotFoundError(Exception):
    """Raised when no FPL entry exists for the given team_id."""


class NoCurrentGameweekError(Exception):
    """Raised when the team exists but has no picks yet (e.g. season hasn't started)."""


def import_team(team_id):
    
    entry_data = get_entry_data(team_id)
    if entry_data is None:
        raise TeamNotFoundError(team_id)

    current_event = entry_data.get("current_event")
    if current_event is None:
        raise NoCurrentGameweekError(team_id)

    picks_data = get_entry_picks(team_id, current_event)
    if picks_data is None:
        raise NoCurrentGameweekError(team_id)

    player_ids = [pick["element"] for pick in picks_data["picks"]]

    return {
        "player_ids": player_ids,
        "manager_name": f"{entry_data['player_first_name']} {entry_data['player_last_name']}",
        "team_name": entry_data["name"],
        "gameweek": current_event,
    }


def main():
    team_id = 390038

    try:
        result = import_team(team_id)
    except TeamNotFoundError:
        print(f"Could not find FPL team with id {team_id}")
        return
    except NoCurrentGameweekError:
        print(f"Team {team_id} has no current gameweek picks yet.")
        return

    print(f"{result['team_name']} ({result['manager_name']}) - GW{result['gameweek']}")
    print(result["player_ids"])


if __name__ == "__main__":
    main()
