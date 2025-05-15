import pandas as pd
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.pkl")
HISTORY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "purchase_history.csv")

# Dummy recommender logic
def get_bundle_recommendation(product_ids):
    df = pd.read_csv(HISTORY_PATH)
    # Filter co-purchased items
    co_purchased = df[df['product_id'].isin(product_ids)]
    co_purchased = co_purchased.groupby('bundle_item_id').size().sort_values(ascending=False)
    top_bundles = co_purchased.head(3).index.tolist()
    return top_bundles
