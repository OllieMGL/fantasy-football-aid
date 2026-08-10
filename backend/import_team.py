from get_data import get_entry_data, get_entry_picks


def import_team(team_id):
    entry_data = get_entry_data(team_id)
    if entry_data is None:
        return None

    current_event = entry_data["current_event"]

    picks_data = get_entry_picks(team_id, current_event)
    if picks_data is None:
        return None

    player_ids = [pick["element"] for pick in picks_data["picks"]]

    return {
        "player_ids": player_ids,
        "manager_name": f"{entry_data['player_first_name']} {entry_data['player_last_name']}",
        "team_name": entry_data["name"],
        "gameweek": current_event,
    }


def main():
    team_id = 6288568

    result = import_team(team_id)
    if result is None:
        print(f"Could not find FPL team with id {team_id}")
        return

    print(f"{result['team_name']} ({result['manager_name']}) - GW{result['gameweek']}")
    print(result["player_ids"])


if __name__ == "__main__":
    main()
