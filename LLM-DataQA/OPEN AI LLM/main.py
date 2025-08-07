import pandas as pd
from pandasai import SmartDataframe
from pandasai.llm import OpenAI

try:
    df = pd.read_csv("student_records.csv")

    llm = OpenAI(api_token="OPEN-AI-API-KEY")
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

