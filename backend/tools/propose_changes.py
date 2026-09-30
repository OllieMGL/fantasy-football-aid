from recommend_player import count_by_club, REQUIRED_COUNTS, BUDGET_LIMIT, MAX_PER_CLUB
from team_scorer import get_players_by_ids

# The one tool that leads to the squad actually changing - but it still doesn't
# change anything itself:
#   1. the model PROPOSES changes (player ids in and out)
#   2. this file CHECKS them against the game's rules
#   3. the user DECIDES, by clicking "Apply" in the frontend
#
# The checks happen in two stages:
#   - check_each_change: is each swap sensible on its own?
#   - check_new_squad:   is the squad legal once EVERY change is made?
# The second stage matters because two swaps can each fit the budget on their
# own and still go over it together.

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "propose_changes",
        "description": (
            "Proposes transfers so the user can apply them with one click. Call this "
            "whenever you recommend specific players to bring in, using the player ids "
            "from the other tools. Each change swaps out_id for in_id; use null for "
            "out_id when filling an empty slot. Returns valid: true if the changes "
            "are allowed, otherwise a list of errors - pick different players and "
            "try again, or explain to the user why it can't be done."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            # null = nobody going out, i.e. filling an empty slot
                            "out_id": {"type": ["integer", "null"]},
                            "in_id": {"type": "integer"},
                        },
                        "required": ["out_id", "in_id"],
                    },
                },
            },
            "required": ["changes"],
        },
    },
}


def player_name(player):
    return f"{player.first_name} {player.second_name}"


def check_each_change(changes, player_ids, players_by_id):
    # stage 1 - looks at each swap on its own, before thinking about the whole squad
    errors = []
    brought_in_so_far = []

    for change in changes:
        out_id = change["out_id"]
        in_id = change["in_id"]

        player_in = players_by_id.get(in_id)

        if player_in is None:
            errors.append(f"No player with id {in_id}.")
            continue

        if in_id in player_ids:
            errors.append(f"{player_name(player_in)} is already in the squad.")

        if in_id in brought_in_so_far:
            errors.append(f"{player_name(player_in)} is being brought in twice.")
        brought_in_so_far.append(in_id)

        if out_id is None:
            continue  # filling an empty slot - so nothing more to check

        if out_id not in player_ids:
            errors.append(f"Player id {out_id} is not in the squad, so can't be taken out.")
            continue

        player_out = players_by_id[out_id]

        if player_out.position != player_in.position:
            errors.append(
                f"Can't swap {player_name(player_out)} ({player_out.position}) for "
                f"{player_name(player_in)} ({player_in.position}) - positions must match."
            )

    return errors


def build_new_squad(changes, player_ids):
    # the squad's ids as they'd be after every change is made
    new_ids = list(player_ids)  # a copy, so the original list isn't changed

    for change in changes:
        if change["out_id"] in new_ids:
            new_ids.remove(change["out_id"])

        new_ids.append(change["in_id"])

    return new_ids


def check_new_squad(new_players, current_players):
    # stage 2 - the rules that only make sense for the squad as a whole
    errors = []

    # no position over its limit
    position_counts = {position: 0 for position in REQUIRED_COUNTS}
    for player in new_players:
        position_counts[player.position] += 1

    for position, count in position_counts.items():
        if count > REQUIRED_COUNTS[position]:
            errors.append(f"That would give {count} {position}, but the max is {REQUIRED_COUNTS[position]}.")

    # max 3 players from any one club
    for team_id, count in count_by_club(new_players).items():
        if count > MAX_PER_CLUB:
            errors.append(f"That would give {count} players from one club (team_id {team_id}), max is {MAX_PER_CLUB}.")

    current_cost = sum(player.now_cost for player in current_players)
    new_cost = sum(player.now_cost for player in new_players)
    budget = max(BUDGET_LIMIT, current_cost)

    # rounded, because adding up prices like 5.1 + 4.3 gives tiny float errors
    if round(new_cost, 1) > round(budget, 1):
        errors.append(f"That would cost £{new_cost:.1f}m, which is over the £{budget:.1f}m budget.")

    return errors


def describe_changes(changes, players_by_id):
    # turns the ids into names and prices the frontend can show on the button
    described = []

    for change in changes:
        player_in = players_by_id[change["in_id"]]

        out_name = None
        if change["out_id"] is not None:
            out_name = player_name(players_by_id[change["out_id"]])

        described.append({
            "out_id": change["out_id"],
            "out_name": out_name,
            "in_id": change["in_id"],
            "in_name": player_name(player_in),
            "in_price": player_in.now_cost,
        })

    return described


def call_propose_changes(changes, player_ids, session):
    if not changes:
        return {"valid": False, "errors": ["No changes were given."]}

    # fetch everyone involved (current squad + everyone coming in) in one query,
    # then keep them in a dict so any player can be looked up by id
    ids_needed = list(player_ids)
    for change in changes:
        ids_needed.append(change["in_id"])

    players_by_id = {}
    for player in get_players_by_ids(ids_needed, session):
        players_by_id[player.id] = player

    errors = check_each_change(changes, player_ids, players_by_id)
    if errors:
        return {"valid": False, "errors": errors}

    new_ids = build_new_squad(changes, player_ids)

    current_players = [players_by_id[pid] for pid in player_ids]
    new_players = [players_by_id[pid] for pid in new_ids]

    errors = check_new_squad(new_players, current_players)
    if errors:
        return {"valid": False, "errors": errors}

    return {"valid": True, "changes": describe_changes(changes, players_by_id)}
