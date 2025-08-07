# 🧠 Smart DataFrame Chatbot

This Python script allows you to interact with a CSV file (`student_records.csv`) using natural language powered by [PandasAI](https://github.com/gventuri/pandas-ai) and OpenAI.

## 📂 Project Structure

```
├── student_records.csv     # Your dataset (replace with your file)
├── main.py                 # Script to run the chatbot
├── requirements.txt        # Dependencies
└── README.md               # This file
```

## 🚀 Features

- Load and process CSV data using Pandas
- Ask questions in natural language (e.g., “What is the average score?”)
- Uses OpenAI LLM through PandasAI
- Command-line interface loop

## 🧰 Requirements

- Python 3.8+
- An OpenAI API key

## 🔧 Setup

1. **Clone this repo (or download the files)**  
2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set your OpenAI API Key**  
Replace `"OPEN-AI-API-KEY"` in `main.py` with your actual key:
```python
llm = OpenAI(api_token="your-api-key-here")
```

4. **Ensure your CSV file is named `student_records.csv` and is in the same folder**

## ▶️ Run the Script

```bash
python main.py
```

Then ask questions like:
```
💬 Ask your question (or press Enter to exit): What is the average score?
```

## 📌 Notes

- The chatbot uses PandasAI to convert natural language into Pandas operations.
- You can customize the CSV file or logic to fit your own datasets.

---

### 🤝 License

This project is provided as-is for educational or experimental use.
