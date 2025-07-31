import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from firebase_admin import firestore

from lc.web_search import web_search
from lc.react_agent import llm
from langchain_core.prompts import ChatPromptTemplate
from api.routes.auth import User, get_current_user

router = APIRouter()

# --- Pydantic Models ---
class NewsSettings(BaseModel):
    enabled: bool
    delivery_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    topics: Optional[List[str]] = []

class ToggleRequest(BaseModel):
    enabled: bool

# --- Helper function for summarization (Unchanged) ---
def _summarize_content_with_llm(content: str, topic: str) -> str:
    print(f"📝 Summarizing content for topic: '{topic}' via LLM...")
    summarization_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert news editor..."""), # Prompt shortened for brevity
        ("user", """**NEWS TOPIC:** "{topic}"\n\n**RAW ARTICLE CONTENT:**\n---\n{content}\n---"""),
    ])
    summarization_chain = summarization_prompt | llm
    try:
        response = summarization_chain.invoke({"topic": topic, "content": content})
        print("✅ Summarization complete.")
        return response.content
    except Exception as e:
        print(f"❌ LLM-based summarization failed: {e}")
        return f"Could not generate an AI summary for '{topic}'.\n" + content[:500] + "..."

# --- Core Function using Firestore ---
def generate_and_save_briefings_for_user(user: User):
    print(f"🚀 Starting news briefing generation for user: {user.uid}...")
    db = firestore.client()
    user_ref = db.collection('users').document(user.uid)
    
    try:
        user_doc = user_ref.get()
        if not user_doc.exists:
            print(f"ℹ️ User {user.uid} not found. Exiting.")
            return {"message": "User not found."}

        user_data = user_doc.to_dict()
        settings = user_data.get("news_settings", {})
        topics = settings.get("topics", [])

        if not settings.get("enabled") or not topics:
            print(f"ℹ️ News briefing is disabled or no topics are set for user {user.uid}. Exiting.")
            return {"message": "News briefing is disabled or no topics are set."}

        today_str = datetime.now().strftime("%Y-%m-%d")
        new_briefings = []

        for topic in topics:
            print(f"\nFetching news for topic: '{topic}'")
            raw_content = web_search.invoke({"query": "latest news in " + topic})
            summary = "Could not fetch content."
            if raw_content and "Error:" not in raw_content:
                summary = _summarize_content_with_llm(raw_content, topic)

            new_briefings.append({"date": today_str, "topic": topic, "summary": summary})

        user_ref.update({"daily_briefings": new_briefings})
        print(f"\n✅ Briefing for user {user.uid} complete and saved to Firestore.")
        return {"message": "News briefing generated successfully."}

    except Exception as e:
        print(f"❌ An error occurred during briefing generation for user {user.uid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- API Endpoints using Firestore ---

@router.get("/briefings/generate")
def trigger_generate_briefings(current_user: User = Depends(get_current_user)):
    """Manually triggers news briefing generation for the authenticated user."""
    return generate_and_save_briefings_for_user(current_user)

@router.get("/briefings/latest")
def get_latest_briefings(current_user: User = Depends(get_current_user)):
    """
    Fetches the latest briefings. If briefings for the current day are not found,
    it automatically generates them first and then returns them.
    """
    db = firestore.client()
    user_ref = db.collection('users').document(current_user.uid)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        return []

    user_data = user_doc.to_dict()
    briefings = user_data.get("daily_briefings", [])
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Check if briefings are missing or outdated
    if not briefings or (briefings and briefings[0].get("date") != today_str):
        print(f"Briefings not found or are outdated for user {current_user.uid}. Generating new ones...")
        # Call the generation function to create and save new briefings
        generate_and_save_briefings_for_user(current_user)
        
        # Re-fetch the document to get the newly created data
        updated_doc = user_ref.get()
        return updated_doc.to_dict().get("daily_briefings", [])
    
    # If briefings exist and are for today, return them
    return briefings

@router.get("/settings")
def get_news_settings(current_user: User = Depends(get_current_user)):
    """Retrieves the news settings for the authenticated user from Firestore."""
    db = firestore.client()
    user_doc = db.collection('users').document(current_user.uid).get()
    if not user_doc.exists:
        return {"enabled": False, "topics": [], "delivery_time": "07:00"}
    return user_doc.to_dict().get("news_settings", {"enabled": False, "topics": []})

@router.post("/settings")
def update_news_settings(settings: NewsSettings, current_user: User = Depends(get_current_user)):
    """Updates the full news settings for the authenticated user in Firestore."""
    db = firestore.client()
    user_ref = db.collection('users').document(current_user.uid)
    user_ref.update({"news_settings": settings.dict()})
    return {"message": "News settings updated successfully."}

@router.post("/settings/toggle")
def toggle_news_feature(request: ToggleRequest, current_user: User = Depends(get_current_user)):
    """Toggles the news feature for the authenticated user in Firestore."""
    db = firestore.client()
    user_ref = db.collection('users').document(current_user.uid)
    user_ref.update({"news_settings.enabled": request.enabled})
    status = "enabled" if request.enabled else "disabled"
    return {"message": f"News briefing feature has been {status}."}