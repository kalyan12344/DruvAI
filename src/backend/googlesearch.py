import requests
import os
from dotenv import load_dotenv
load_dotenv()

def google_search(query, max_results=3):
    api_key = os.getenv("GOOGLE_API_KEY")
    cx_id = os.getenv("GOOGLE_CX_ID")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx_id,
        "q": query,
        "num": max_results
    }

    try:
        res = requests.get(url, params=params)
        items = res.json().get("items", [])
        if not items:
            return "🔍 No relevant results found."

        return "\n\n".join([
            f"🔗 *{item['title']}*\n{item['snippet']}\n{item['link']}"
            for item in items
        ])

    except Exception as e:
        print("Google search error:", e)
        return "❌ Failed to perform search."
