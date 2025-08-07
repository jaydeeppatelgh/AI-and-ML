# LLM CSV Reader with Local Ollama

This project lets you ask questions about your CSV (and optionally PDF) data using a local Large Language Model (LLM) via Ollama and LangChain. It loads your data, splits it into chunks, creates embeddings for semantic search, and uses a local LLM to answer your questions interactively.

## Features
- Load and combine multiple CSV files (and optionally PDF files)
- Split large text into manageable chunks for better AI processing
- Create vector embeddings for semantic search
- Use a local Ollama LLM (like Llama 3) for question answering
- Interactive command-line interface for asking questions

## Requirements

- Python 3.8+
- [Ollama](https://ollama.com/) installed and running locally
- Python packages:
  - pandas
  - pdfplumber
  - langchain
  - langchain-community
  - langchain-ollama

## Installation

1. **Clone this repository** (or download the files):
   ```sh
   git clone <your-repo-url>
   cd my_llm_csv_reader
   ```

2. **Install Python dependencies:**
   ```sh
   pip install pandas pdfplumber langchain langchain-community langchain-ollama
   ```

3. **Install and start Ollama:**
   - Download and install from [Ollama's website](https://ollama.com/download)
   - Start Ollama and pull the Llama 3 model:
     ```sh
     ollama run llama3
     ```

4. **Prepare your data:**
   - Place your CSV files in the `csv/` folder (e.g., `space_missions.csv`, `student_records.csv`, `ai_financial_data.csv`).
   - (Optional) Place PDF files in the `pdf/` folder.

## How It Works

1. **Data Loading:**
   - Reads CSV files using pandas and (optionally) PDF files using pdfplumber.
2. **Text Splitting:**
   - Splits the combined text into smaller overlapping chunks for better AI processing.
3. **Embeddings & Vector Store:**
   - Converts text chunks into vector embeddings using HuggingFace models.
   - Stores them in a Chroma vector store for fast semantic search.
4. **LLM Setup:**
   - Uses Ollama to run a local Llama 3 model for answering questions.
5. **Retrieval QA Chain:**
   - Connects the retriever and LLM so the model answers questions based on your data.
6. **Interactive CLI:**
   - Lets you ask questions in a loop and get answers from your data.

## Usage

1. **Start Ollama** (if not already running):
   ```sh
   ollama run llama3
   ```

2. **Run the script:**
   ```sh
   python main.py
   ```

3. **Ask questions:**
   - Type your question and press Enter.
   - Type `exit` to quit.

## Example

```
Ask a question (or type 'exit'): How many space missions are listed?
🧠 There are 10 space missions listed in the data.

Ask a question (or type 'exit'): List all students with grade A.
🧠 The students with grade A are: Alice, Bob, and Carol.
```

## Customization

- To add more CSV or PDF files, place them in the respective folders and update the file paths in `main.py`.
- You can change the chunk size or overlap in the `RecursiveCharacterTextSplitter` for different data sizes.
- Try different models by changing the model name in `OllamaLLM(model="llama3")`.

## File Overview

- `main.py` — Main script for loading data and running the QA loop
- `csv/` — Folder for your CSV data files
- `pdf/` — Folder for your PDF data files (optional)
- `flowchart.png` — (If present) Visual overview of the data flow

## Troubleshooting

- Make sure Ollama is running and the model is downloaded before starting the script.
- If you get errors about missing packages, install them with pip.
- For large files, increase memory or adjust chunk sizes.

## Credits

- Built with [LangChain](https://python.langchain.com/), [Ollama](https://ollama.com/), and [HuggingFace Embeddings](https://huggingface.co/).
