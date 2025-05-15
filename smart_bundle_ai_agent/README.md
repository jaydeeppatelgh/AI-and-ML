# Smart Bundle AI Agent

Smart Bundle AI is a lightweight e-commerce personalization agent that suggests product bundles based on a customer's current cart or viewed product IDs. It uses co-purchase history to recommend relevant additional items, improving Average Order Value (AOV) and enhancing the shopping experience.

## 🧠 Key Features

- Recommends bundles using historical co-purchase data
- Real-time suggestion via a web interface
- Simple and modular Flask backend
- Easily extendable with ML models or APIs

---

## 🚀 How to Use

### 1. Clone the Repository

```bash
git clone <repo-url>
cd smart_bundle_ai
```

### 2. Create a Virtual Environment (optional)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the App

```bash
python run.py
```

Visit `http://127.0.0.1:5000` in your browser.

---

## 📊 Example

Enter product IDs like:
```
101, 102
```

The system will respond with bundled recommendations such as:
```
Recommended Bundle: 201, 202
```

---

## 🧩 How it Works

- Uses `purchase_history.csv` to simulate real co-purchase behavior.
- `recommender.py` filters and ranks the most common bundle items.
- Frontend sends product IDs via AJAX and displays suggestions.

---

## 📌 To-Do (Extendable Ideas)

- Integrate real-time customer session tracking
- Add machine learning models for smarter prediction
- Connect to live product data via API
- Deploy to Heroku, Render, or Railway

