import requests

#postion key in the fpl API
# 1 = goalkeeper 
# 2 = defender 
# 3 = midfielder
# 4 = forward


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
print(fpl_data["elements"][0])