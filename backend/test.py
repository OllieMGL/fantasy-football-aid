import requests

base_url = "https://fantasy.premierleague.com/api"

def get_default_player_data():
    url = f"{base_url}/bootstrap-static/"
    response = requests.get(url)

    if response.status_code == 200:
        fpl_data = response.json()
        return fpl_data

    else:
        print("Failed to return data")
    
    

fpl_data = get_default_player_data()