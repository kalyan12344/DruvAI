#lc/config.py

import os
from langchain_openai import ChatOpenAI 
import json
from dotenv import load_dotenv
load_dotenv()

def get_llm():
    return ChatOpenAI(
        # model="mistralai/mistral-7b-instruct",
        model = "mistralai/devstral-small",
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )


def get_llm_for_categorization():
    """
    Returns a specialized LLM for email categorization.
    """
    return ChatOpenAI(
        model="qwen/qwen3-8b",
        temperature=0,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )