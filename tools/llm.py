import os
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment (.env)")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
    return ChatGoogleGenerativeAI(model=model, api_key=api_key, temperature=0.2)
