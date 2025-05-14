import os
import requests
from geopy.distance import geodesic
from core.utils import get_travel_time
import joblib

model = joblib.load('model/station_recommender.pkl')

def fetch_real_time_stations(lat, lng, radius_km=10):
    url = "https://api.openchargemap.io/v3/poi/"
    params = {
        'output': 'json',
        'latitude': lat,
        'longitude': lng,
        'distance': radius_km,
        'distanceunit': 'KM',
        'maxresults': 10,
    }
    headers = {'X-API-Key': os.getenv('OCM_API_KEY')}
    response = requests.get(url, params=params, headers=headers)
    return response.json()

def ml_score_station(distance_km, travel_time_sec, available_slots):
    return model.predict([[distance_km, travel_time_sec, available_slots]])[0]

def recommend_station(user_lat, user_lng, battery_level):
    stations = fetch_real_time_stations(user_lat, user_lng)
    user_location = (user_lat, user_lng)

    scored = []
    for station in stations:
        if not station.get("AddressInfo"): continue
        lat = station["AddressInfo"]["Latitude"]
        lng = station["AddressInfo"]["Longitude"]
        dest = (lat, lng)
        distance = geodesic(user_location, dest).km
        travel_time = get_travel_time(user_location, dest, os.getenv('GOOGLE_API_KEY'))
        available_slots = station.get("NumberOfPoints", 1)
        score = ml_score_station(distance, travel_time, available_slots)
        scored.append((score, {
            "name": station["AddressInfo"].get("Title"),
            "distance_km": round(distance, 2),
            "travel_time_sec": travel_time,
            "available_slots": available_slots
        }))

    if not scored:
        return None

    scored.sort()
    return scored[0][1]
