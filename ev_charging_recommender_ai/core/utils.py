import requests

def get_travel_time(origin, destination, api_key):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        'origins': f"{origin[0]},{origin[1]}",
        'destinations': f"{destination[0]},{destination[1]}",
        'key': api_key,
        'departure_time': 'now',
    }
    res = requests.get(url, params=params).json()
    try:
        return res["rows"][0]["elements"][0]["duration"]["value"]
    except:
        return float('inf')
