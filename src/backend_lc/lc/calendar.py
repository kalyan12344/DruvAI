# lc/calendar.py
"""
Google-Calendar utilities exposed as LangChain tools.
Relies on core.google_auth.get_calendar_service() already in your codebase.
"""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from lc.config import get_llm
from core.google_auth import get_calendar_service
import re

CHICAGO_TZ = ZoneInfo("America/Chicago")
TODAY = datetime.now(CHICAGO_TZ).strftime("%Y-%m-%d")

# ─────────── Standard Function (Not a Tool) ────────────────────────
def get_all_events(user_id: str, max_results: int = 250) -> list:
    """
    Fetches all upcoming calendar events for a specific user as a standard Python function.
    """
    print(f"Fetching up to {max_results} upcoming events for user {user_id}...")
    now = datetime.now(CHICAGO_TZ).isoformat()
    service = get_calendar_service(user_id=user_id)
    
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=now, 
        maxResults=max_results, 
        singleEvents=True, 
        orderBy='startTime'
    ).execute()
    
    items = events_result.get('items', [])
    print(f"Successfully fetched {len(items)} events.")
    return items

# ─────────── LangChain Tools ───────────────────────────────────────
# NOTE: The user_id must be passed by the agent runner when invoking these tools.

class FindDatesArgs(BaseModel):
    text: str = Field(..., description="Free-text with a date expression")

@tool(args_schema=FindDatesArgs)
def find_dates(text: str) -> dict:
    """
    Parse natural-language schedule text into structured pieces if user says next friday or next month or next week if the user doesnot mention the exact date use this.
    """
    prompt = f"""Today is {TODAY}. Week starts on Sunday.
Sentence: "{text}"

Respond ONLY as:
{{"title":"","date":"YYYY-MM-DD","time":"HH:MM","duration_minutes":60}}
"""
    return json.loads(get_llm().invoke(prompt).content.strip())

@tool
def get_current_date() -> str:
    """
    Get the current date in YYYY-MM-DD format based on the America/Chicago timezone.
    """
    return datetime.now(CHICAGO_TZ).strftime("%Y-%m-%d")

class EventsOnArgs(BaseModel):
    user_id: str = Field(..., description="The ID of the user for whom to fetch events.")
    date: str = Field(..., description="The date to fetch events for in YYYY-MM-DD format.")

@tool(args_schema=EventsOnArgs)
def get_events_on_date(user_id: str, date: str) -> dict:
    """
    Return a structured JSON object containing a list of all events on a specific date.
    For natural language dates (e.g., 'tomorrow'), you MUST use the 'find_dates' tool FIRST.
    The date input MUST be in YYYY-MM-DD format.
    """
    try:
        service = get_calendar_service(user_id=user_id)
        day_start = datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)
        day_end = datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)

        items = service.events().list(
            calendarId="primary",
            timeMin=day_start.isoformat(), 
            timeMax=day_end.isoformat(),
            singleEvents=True, 
            orderBy="startTime"
        ).execute().get("items", [])

        if not items:
            return {"status": f"🎉 You’re free on {date}", "events": []}

        simplified_events = [{
            "summary": event.get("summary", "(No title)"),
            "start": event.get("start"),
            "end": event.get("end"),
            "id": event.get("id")
        } for event in items]
    
        return {"status": f"Found {len(simplified_events)} events on {date}.", "events": simplified_events}

    except Exception as e:
        return {"status": f"An error occurred: {str(e)}", "events": []}

class CreateArgs(BaseModel):
    user_id: str = Field(..., description="The ID of the user for whom to create the event.")
    description: str = Field(..., description="Sentence describing the event, like 'Meeting with Bob tomorrow at 3pm'.")

@tool(args_schema=CreateArgs)
def create_event(user_id: str, description: str) -> str:
    """Create a calendar event from natural language for a specific user."""
    data = find_dates.run({"text": description})
    title = data["title"]
    date, time = data["date"], data["time"]
    dur   = int(data.get("duration_minutes", 60))
    
    service = get_calendar_service(user_id=user_id)

    if time and time != "00:00":
        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").astimezone(CHICAGO_TZ)
        end_dt   = start_dt + timedelta(minutes=dur)
        body = {
            "summary": title,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "America/Chicago"},
            "end":   {"dateTime": end_dt.isoformat(),   "timeZone": "America/Chicago"},
        }
    else:
        body = { "summary": title, "start": {"date": date}, "end": {"date": date} }
    
    service.events().insert(calendarId="primary", body=body).execute()
    return f"✅ '{title}' created on {date}{' at '+time if time!='00:00' else ''}"

class DeleteArgs(BaseModel):
    user_id: str = Field(..., description="The ID of the user for whom to delete the event.")
    instruction: str = Field(..., description="Instruction to delete an event, e.g., \"'Event Title' on YYYY-MM-DD\"")

@tool(args_schema=DeleteArgs)
def delete_event(user_id: str, instruction: str) -> str:
    """Delete an event by its exact title and date for a specific user."""
    if " on " not in instruction.lower():
        return "⚠️ Instruction format error. Please provide as: <title> on YYYY-MM-DD"
    
    parsed_title_part, date_str = instruction.rsplit(" on ", 1)
    final_title = parsed_title_part.strip().strip("'\" ")
    date_str = date_str.strip()

    service = get_calendar_service(user_id=user_id)
    day_start = datetime.strptime(f"{date_str} 00:00:00", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)
    day_end = datetime.strptime(f"{date_str} 23:59:59", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)

    events = service.events().list(
        calendarId="primary",
        timeMin=day_start.isoformat(),
        timeMax=day_end.isoformat(),
        singleEvents=True
    ).execute().get("items", [])

    event_to_delete = next((ev for ev in events if ev.get("summary", "").lower() == final_title.lower()), None)

    if event_to_delete:
        service.events().delete(calendarId="primary", eventId=event_to_delete["id"]).execute()
        return f"🗑️ Successfully deleted event: '{event_to_delete.get('summary', final_title)}' on {date_str}."
    else:
        return f"❌ No event found with the exact title '{final_title}' on {date_str} to delete."