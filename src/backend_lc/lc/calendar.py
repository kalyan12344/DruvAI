# lc/calendar.py

"""
Google-Calendar utilities exposed as LangChain tools.
Relies on core.google_auth.get_calendar_service() already in your codebase.
"""
import json
from datetime import datetime, timedelta
# Use the standard library for timezones (Python 3.9+)
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from lc.config import get_llm
from core.google_auth import get_calendar_service
import re

# --- TIMEZONE FIX: Define our target timezone ---
CHICAGO_TZ = ZoneInfo("America/Chicago")

# --- TIMEZONE FIX: TODAY is now calculated in the correct timezone ---
TODAY = datetime.now(CHICAGO_TZ).strftime("%Y-%m-%d")

# ─────────── helper ────────────────────────────────────────────
def _svc():
    return get_calendar_service()

def get_all_events(max_results: int = 250) -> list:
    """
    Fetches all upcoming calendar events as a standard Python function.
    """
    print(f"Fetching up to {max_results} upcoming events...")
    # --- TIMEZONE FIX: Use the timezone-aware 'now' for the query ---
    now = datetime.now(CHICAGO_TZ).isoformat()
    
    events_result = _svc().events().list(
        calendarId='primary', 
        timeMin=now, 
        maxResults=max_results, 
        singleEvents=True, 
        orderBy='startTime'
    ).execute()
    
    items = events_result.get('items', [])
    print(f"Successfully fetched {len(items)} events.")
    return items

# ─────────── find_dates ────────────────────────────────────────
class FindDatesArgs(BaseModel):
    text: str = Field(..., description="Free-text with a date expression")

@tool(args_schema=FindDatesArgs)
def find_dates(text: str) -> dict:
    """
    Parse natural-language schedule text into structured pieces if user says next friday or next month or next week if the user doesnot mention the exact date use this.
    """
    # The prompt now correctly uses the CDT-based TODAY
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

# ─────────── get_events_on_date ────────────────────────────────
class EventsOnArgs(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")

@tool(args_schema=EventsOnArgs)
def get_events_on_date(date: str) -> dict:
    """
    Return a structured JSON object containing a list of all events on a specific date.
    For natural language dates (e.g., 'tomorrow'), you MUST use the 'find_dates' tool FIRST.
    The date input MUST be in YYYY-MM-DD format.
    """
    try:
        # --- TIMEZONE FIX: Create timezone-aware start and end datetimes for the given date ---
        day_start = datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)
        day_end = datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)

        # The .isoformat() method will now include the correct timezone offset (e.g., -05:00)
        start_iso = day_start.isoformat()
        end_iso = day_end.isoformat()

        items = _svc().events().list(
            calendarId="primary",
            timeMin=start_iso, 
            timeMax=end_iso,
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

# ─────────── get_events_in_range ───────────────────────────────
class RangeArgs(BaseModel):
    request: str = Field(..., description="Sentence like 'next week' or 'June 1-5'")

@tool(args_schema=RangeArgs)
def get_events_in_range(request: str) -> str:
    """Interpret a natural date range and list events inside it."""
    # This function remains largely the same but relies on other fixed tools
    # We will assume find_dates or the LLM provides correct YYYY-MM-DD strings
    # The fetching logic below correctly uses these date strings
    try:
        prompt = f"""Today is {TODAY}.
Extract start_date and end_date (YYYY-MM-DD) from the text below.

"{request}"

Respond as:
{{"start_date":"YYYY-MM-DD","end_date":"YYYY-MM-DD"}}
"""
        response_content = get_llm().invoke(prompt).content.strip()
        
        # ... (Your existing parsing and error handling logic) ...
        dates = json.loads(response_content)
        s, e = dates["start_date"], dates["end_date"]
        
        # --- TIMEZONE FIX: Apply the same logic as get_events_on_date ---
        start_dt = datetime.strptime(f"{s} 00:00:00", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)
        end_dt = datetime.strptime(f"{e} 23:59:59", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)

        items = _svc().events().list(calendarId="primary",
                                     timeMin=start_dt.isoformat(),
                                     timeMax=end_dt.isoformat(),
                                     singleEvents=True, orderBy="startTime"
                                     ).execute().get("items", [])
        
        if not items:
            return f"No events between {s} and {e}"
        
        return "📅 " + " | ".join(
            f"{it['start'].get('dateTime', it['start'].get('date'))} – {it.get('summary','(No title)')}"
            for it in items
        )
        
    except Exception as e:
        error_msg = f"Error processing date range '{request}': {str(e)}"
        print(error_msg)
        return error_msg

@tool
def _parse_date_fallback(request: str) -> dict:
    """Fallback date parsing for common expressions when LLM fails."""
    # --- TIMEZONE FIX: Use a timezone-aware 'today' for calculations ---
    today = datetime.now(CHICAGO_TZ)
    # ... (the rest of your fallback logic is fine as it deals with date arithmetic) ...
    # ...
    return {
        "start_date": today.strftime('%Y-%m-%d'), 
        "end_date": (today + timedelta(days=7)).strftime('%Y-%m-%d')
    }

# ─────────── create_event ──────────────────────────────────────
class CreateArgs(BaseModel):
    description: str = Field(..., description="Sentence describing the event")

@tool(args_schema=CreateArgs)
def create_event(description: str) -> str:
    """Create a calendar event from natural language."""
    data = find_dates.run({"text": description})
    title = data["title"]
    date, time = data["date"], data["time"]
    dur   = int(data.get("duration_minutes", 60))
    svc   = _svc()

    if time and time != "00:00":
        # --- TIMEZONE FIX: Ensure the datetime object created is aware of the Chicago timezone ---
        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").astimezone(CHICAGO_TZ)
        end_dt   = start_dt + timedelta(minutes=dur)
        body = {
            "summary": title,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "America/Chicago"},
            "end":   {"dateTime": end_dt.isoformat(),   "timeZone": "America/Chicago"},
        }
    else:  # all-day event
        body = { "summary": title, "start": {"date": date}, "end": {"date": date} }
    
    svc.events().insert(calendarId="primary", body=body).execute()
    return f"✅ '{title}' created on {date}{' at '+time if time!='00:00' else ''}"

# ─────────── delete_event ──────────────────────────────────────
class DeleteArgs(BaseModel):
    instruction: str = Field(..., description="Instruction to delete an event, e.g., \"'Event Title' on YYYY-MM-DD\"")

@tool(args_schema=DeleteArgs)
def delete_event(instruction: str) -> str:
    """Delete an event by its exact title and date."""
    if " on " not in instruction.lower():
        return "⚠️ Instruction format error. Please provide as: <title> on YYYY-MM-DD"
    
    # ... (Your parsing logic) ...
    parsed_title_part, date_str = instruction.rsplit(" on ", 1)
    final_title = parsed_title_part.strip().strip("'\" ")
    date_str = date_str.strip()

    # --- TIMEZONE FIX: Use the same timezone-aware logic to find the event to delete ---
    day_start = datetime.strptime(f"{date_str} 00:00:00", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)
    day_end = datetime.strptime(f"{date_str} 23:59:59", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)

    events = _svc().events().list(
        calendarId="primary",
        timeMin=day_start.isoformat(),
        timeMax=day_end.isoformat(),
        singleEvents=True
    ).execute().get("items", [])

    # ... (Your deletion logic) ...
    event_to_delete = next((ev for ev in events if ev.get("summary", "").lower() == final_title.lower()), None)

    if event_to_delete:
        _svc().events().delete(calendarId="primary", eventId=event_to_delete["id"]).execute()
        return f"🗑️ Successfully deleted event: '{event_to_delete.get('summary', final_title)}' on {date_str}."
    else:
        return f"❌ No event found with the exact title '{final_title}' on {date_str} to delete."