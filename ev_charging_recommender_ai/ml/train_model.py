import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

data = pd.DataFrame({
    'distance_km': [1, 2, 3, 4, 5],
    'travel_time_sec': [300, 600, 900, 1200, 1500],
    'available_slots': [1, 2, 0, 3, 1],
    'user_score': [9, 8, 3, 7, 6]
})

X = data[['distance_km', 'travel_time_sec', 'available_slots']]
y = data['user_score']

model = RandomForestRegressor(n_estimators=10)
model.fit(X, y)
joblib.dump(model, 'model/station_recommender.pkl')
