import json
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional

from datetime import datetime
from lc.web_search import web_search
from lc.react_agent import llm # Import the LLM directly
from langchain_core.prompts import ChatPromptTemplate

router = APIRouter()

# --- Pydantic Models for Type Safety ---

class NewsSettings(BaseModel):
    """Defines the full settings structure."""
    enabled: bool
    delivery_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$") # HH:MM format
    topics: Optional[List[str]] = []

class ToggleRequest(BaseModel):
    """Defines the simple request body for the toggle endpoint."""
    enabled: bool

# --- Helper function to read/write JSON to avoid code duplication ---

def _read_db():
    """Reads the entire db.json file."""
    try:
        with open("db.json", 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is empty, return a default structure
        return {
            "news_briefing_settings": {"enabled": False, "topics": [], "delivery_time": "07:00"},
            "daily_briefings": []
        }

def _write_db(data):
    """Writes the entire data object back to db.json."""
    with open("db.json", 'w') as f:
        json.dump(data, f, indent=2)


def _summarize_content_with_llm(content: str, topic: str) -> str:
    """
    Summarizes the raw text content by calling the LLM directly with a structured prompt.
    This is more reliable for a direct summarization task than using the full agent.
    """
    print(f"📝 Summarizing content for topic: '{topic}' via LLM...")

    # Create a detailed prompt for the LLM to summarize the news content.
    summarization_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert news editor. Your task is to scan a large block of raw text from multiple articles and extract several distinct news headlines.

**CRITICAL INSTRUCTIONS:**
1.  **Primary Goal:** Identify 3 to 5 unique news stories from the provided text.
2.  **Format:** Present the output as a bulleted list. For each item, provide a **compelling headline** on the first line, and a **single descriptive sentence** on the next line, indented slightly.
3.  **Content:** Each headline must be different. Do not repeat the same news event. For example, if the topic is "AI", find headlines about different companies or advancements, not just Google.
4.  **Tone:** Headlines should be clear, concise, and professional.
5.  **Constraint:** Base your headlines ONLY on the text provided below."""),
        ("user", """**NEWS TOPIC:**
"{topic}"

**RAW ARTICLE CONTENT FOR CONTEXT:**
---
{content}
---

Now, generate the list of distinct headlines following all instructions precisely.""")
    ])

    # Create a simple chain: prompt -> llm -> output
    summarization_chain = summarization_prompt | llm

    try:
        # Call the chain with the content and topic
        response = summarization_chain.invoke({"topic": topic, "content": content})
        summary = response.content
        print("✅ Summarization complete.")
        return summary
    except Exception as e:
        print(f"❌ LLM-based summarization failed: {e}")
        # Fallback to a simple truncation if the LLM fails
        return f"Could not generate an AI summary for '{topic}'.\n" + content[:500] + "..."


# --- Core Functions ---

def generate_and_save_briefings():
    """
    The main function to be run by the scheduler or on-demand.
    It reads topics from db.json, fetches news for each, summarizes it,
    and saves the new briefings back to db.json.
    """
    print("🚀 Starting daily news briefing generation...")
    try:
        db_data = _read_db()
        settings = db_data.get("news_briefing_settings", {})
        topics = settings.get("topics", [])

        if not settings.get("enabled") or not topics:
            print("ℹ️ News briefing is disabled or no topics are set. Exiting.")
            return {"message": "News briefing is disabled or no topics are set."}

        today_str = datetime.now().strftime("%Y-%m-%d")
        new_briefings = []

        for topic in topics:
            print(f"\nFetching news for topic: '{topic}'")
            # The web_search tool is now called with .invoke() as per modern LangChain standards.
            raw_content = web_search.invoke({"query": topic})

            if "Error:" in raw_content or "No search results" in raw_content:
                summary = f"Could not generate a briefing for '{topic}'. Reason: {raw_content}"
            else:
                summary = _summarize_content_with_llm(raw_content, topic)

            new_briefings.append({
                "date": today_str,
                "topic": topic,
                "summary": summary
            })

        db_data["daily_briefings"] = new_briefings
        _write_db(db_data)
        print("\n✅ Daily news briefing generation complete and saved to db.json.")
        return {"message": "News briefing generated successfully."}

    except Exception as e:
        print(f"❌ An error occurred during briefing generation: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during briefing generation: {e}")


# --- API Endpoints ---

@router.get("/briefings/generate")
def trigger_generate_briefings():
    """
    An endpoint to manually trigger the news briefing generation.
    Used by the "Refresh Now" button.
    """
    return generate_and_save_briefings()


@router.get("/briefings/latest")
def get_latest_briefings():
    """
    Fetches the most recently stored daily briefings from the database.
    This is used for the initial page load.
    """
    db_data = _read_db()
    return db_data.get("daily_briefings", [])


@router.get("/settings")
def get_news_settings():
    """
    Retrieves the current news briefing settings.
    """
    db_data = _read_db()
    return db_data.get("news_briefing_settings", {"enabled": False, "topics": []})


@router.post("/settings")
def update_news_settings(settings: NewsSettings):
    """
    Updates the user's full news briefing settings (topics, enabled state, time).
    """
    try:
        db_data = _read_db()
        db_data["news_briefing_settings"] = settings.dict()
        _write_db(db_data)
        return {"message": "News settings updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/settings/toggle")
def toggle_news_feature(request: ToggleRequest):
    """
    Specifically handles turning the news feature on or off.
    """
    try:
        db_data = _read_db()
        if "news_briefing_settings" not in db_data:
            db_data["news_briefing_settings"] = {"topics": [], "delivery_time": "07:00"}
        db_data["news_briefing_settings"]["enabled"] = request.enabled
        _write_db(db_data)
        status = "enabled" if request.enabled else "disabled"
        return {"message": f"News briefing feature has been {status}."}
    except Exception as e:
        print(f"Error in /settings/toggle: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
