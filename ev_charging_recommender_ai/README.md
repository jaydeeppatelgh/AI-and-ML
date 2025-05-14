
# 🔌 EV Charging Recommender AI Agent

This project is a Python-based intelligent agent that recommends the best nearby EV charging station based on:
- Real-time station data from OpenChargeMap
- Live traffic-aware travel time from Google Maps API
- Charging point availability
- Machine Learning model that ranks stations by predicted user preference

---

## 🧠 How It Works

1. **User Input:** Latitude, Longitude, and Battery level via API call
2. **Station Fetching:** Pulls real-time nearby EV stations using OpenChargeMap
3. **Travel Estimation:** Uses Google Maps Distance Matrix API to calculate live ETA
4. **Scoring:** ML model (Random Forest) scores each station using:
   - Distance (km)
   - Travel time (sec)
   - Available slots
5. **Recommendation:** Returns the highest-ranked station as JSON

---

## 🔧 Setup Instructions

### 1. Clone the Repo
```bash
git clone https://github.com/yourname/ev_charging_recommender_ai.git
cd ev_charging_recommender_ai
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Your API Keys
Create a `.env` file in the root folder:
```env
GOOGLE_API_KEY=your_google_maps_api_key
OCM_API_KEY=your_open_charge_map_api_key
```

### 4. Train the ML Model
```bash
python ml/train_model.py
```

### 5. Run the API
```bash
python api/app.py
```

The API will start at: [http://localhost:5000/recommend](http://localhost:5000/recommend)

---

## 📡 API Endpoint

### `GET /recommend`

| Parameter | Type    | Required | Description                    |
|-----------|---------|----------|--------------------------------|
| `lat`     | float   | ✅       | Latitude of the user location |
| `lng`     | float   | ✅       | Longitude of the user         |
| `battery` | float   | ✅       | Current battery percentage    |

#### Example
```bash
curl "http://localhost:5000/recommend?lat=37.77&lng=-122.42&battery=30"
```

---

## 🧪 Testing

You can use tools like **Postman**, **curl**, or simply hit the endpoint via browser (GET) for quick tests.

---

## 🚀 Deployment

You can deploy this API on:
- [Render](https://render.com)
- [Railway](https://railway.app)
- [Heroku](https://heroku.com)

**Start Command (for Gunicorn)**:
```bash
gunicorn api.app:app
```

---

## 📌 Notes

- The ML model is simplistic and trained on mock data. Replace with real usage logs for production-grade accuracy.
- The app gracefully handles API failures with fallback logic.
- You can improve station ranking by incorporating:
  - User history
  - Charging costs
  - Charger types (Level 2, Level 3)
