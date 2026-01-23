import os
import pandas as pd
from pandasai import SmartDataframe
from pandasai.llm import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    df = pd.read_csv("trades.csv")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file.")
    
    llm = OpenAI(api_token=api_key)
    sdf = SmartDataframe(df, config={"llm": llm, "verbose": False, "enable_cache": False})

    # Start chat loop
    while True:
        question = input("\n💬 Ask your question (or press Enter to exit): ").strip()
        if question == "":
            print("👋 Exiting the chat. Goodbye!")
            break

        try:
            answer = sdf.chat(question)
            print("\n🔍 Answer:")
            print(answer)
        except Exception as e:
            print("❌ Failed to get answer:", e)

except Exception as e:
    print("\n❌ ERROR OCCURRED:")
    print(e)

