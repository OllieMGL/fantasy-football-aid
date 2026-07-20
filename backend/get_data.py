import requests

#postion key in the fpl API
# 1 = goalkeeper 
# 2 = defender 
# 3 = midfielder
# 4 = forward

# NEED TO REPOPULATE / RESET DATABASE FOR NEW SEASON - currently have 25/26 season data


BASE_URL = "https://fantasy.premierleague.com/api"

def get_default_data():
    url = f"{BASE_URL}/bootstrap-static/"
    response = requests.get(url)

    if response.status_code == 200:
        fpl_data = response.json()
        return fpl_data

    else:
        print("Failed to return data")

def get_fixture_data():
    
    url = f"{BASE_URL}/fixtures/"
    response = requests.get(url)

    if response.status_code == 200:
        fixture_data = response.json()
        return fixture_data
    else:
        print("Failed to return data")


def get_player_by_ID(playerID):
    
    url = f"{BASE_URL}/element-summary/{playerID}/"
    response = requests.get(url)

    if response.status_code == 200:
        player_data = response.json()
        return player_data
    else:
        print("Failed to return data")


