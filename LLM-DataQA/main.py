import os
import pandas as pd
import pdfplumber
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_ollama import OllamaLLM

def load_pdf(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

def format_csv_for_llm(path):
    df = pd.read_csv(path)
    rows = df.to_dict(orient="records")
    formatted_rows = []
    for row in rows:
        formatted = ", ".join([f"{k}: {v}" for k, v in row.items()])
        formatted_rows.append(f"Record => {formatted}")  
    return "\n".join(formatted_rows)

print("Loading data...")

pdf_data = load_pdf("ai_models.pdf")
# csv_data = format_csv_for_llm("csv/student_records.csv")
full_text =  pdf_data

# --- Split Data ---
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
chunks = splitter.create_documents([full_text])
# print(f"Chunks created: {chunks}")
# print(f"Total chunks created: {len(chunks)}")

# --- Embeddings + Vector Store ---
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(chunks, embedding)
retriever = vectorstore.as_retriever(search_kwargs={"k": 100})

# --- Local Ollama Model ---
llm = OllamaLLM(model="llama3")

# --- QA Chain ---
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

# --- Ask Questions ---
# while True:
#     query = input("\nAsk a question (or type 'exit'): ")
#     if query.lower() == "exit":
#         break
#     answer = qa_chain.invoke({"query": query})
#     print("🧠", answer["result"])
    # answer = qa_chain.run(query)
    # print("🧠", answer)