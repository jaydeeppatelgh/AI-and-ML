from flask import Flask, render_template, request, jsonify
from app.recommender import get_bundle_recommendation

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    product_ids = data.get("product_ids", [])
    recommendations = get_bundle_recommendation(product_ids)
    return jsonify({"bundle": recommendations})

if __name__ == '__main__':
    app.run(debug=True)
