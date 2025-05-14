from flask import Flask, request, jsonify
from core.recommender import recommend_station
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

@app.route('/recommend', methods=['GET'])
def recommend():
    try:
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
        battery = float(request.args.get('battery'))
        station = recommend_station(lat, lng, battery)
        return jsonify({"recommended_station": station})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
