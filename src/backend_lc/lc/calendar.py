import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from lc.config import get_llm
from core.google_auth import get_calendar_service

CHICAGO_TZ = ZoneInfo("America/Chicago")
TODAY = datetime.now(CHICAGO_TZ).strftime("%Y-%m-%d")

def get_all_events(user_id: str, max_results: int = 250) -> list:
    """Fetches all upcoming calendar events for a specific user as a standard Python function."""
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

class FindDatesArgs(BaseModel):
    text: str = Field(..., description="Free-text with a date expression")

@tool(args_schema=FindDatesArgs)
def find_dates(text: str) -> dict:
    """Parses a natural language string containing date and time information (e.g., 'meeting tomorrow at 3pm') into a structured JSON object."""
    prompt = f"""Today is {TODAY}. Week starts on Sunday.
Sentence: "{text}"
Respond ONLY as JSON: {{"title":"","date":"YYYY-MM-DD","time":"HH:MM","duration_minutes":60}}"""
    return json.loads(get_llm().invoke(prompt).content.strip())

@tool
def get_current_date() -> str:
    """Gets the current date in YYYY-MM-DD format based on the America/Chicago timezone."""
    return datetime.now(CHICAGO_TZ).strftime("%Y-%m-%d")

class EventsOnArgs(BaseModel):
    date: str = Field(..., description="The date to fetch events for in YYYY-MM-DD format.")

@tool(args_schema=EventsOnArgs)
def get_events_on_date(*, date: str, user_id: str) -> dict:
    """Returns a list of all calendar events for a user on a given date. The date MUST be in 'YYYY-MM-DD' format. For natural language dates like 'tomorrow', the 'find_dates' tool must be used first to get the correct format."""
    try:
        service = get_calendar_service(user_id=user_id)
        day_start = datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)
        day_end = datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)

        items = service.events().list(
            calendarId="primary",
            timeMin=day_start.isoformat(), 
            timeMax=day_end.isoformat(), # <-- THIS WAS THE FIX
            singleEvents=True, 
            orderBy="startTime"
        ).execute().get("items", [])

        if not items:
            return {"status": f"You’re free on {date}", "events": []}

        simplified_events = [{"summary": e.get("summary", "(No title)"), "start": e.get("start"), "end": e.get("end"), "id": e.get("id")} for e in items]
        return {"status": f"Found {len(simplified_events)} events on {date}.", "events": simplified_events}
    except Exception as e:
        return {"status": f"An error occurred: {str(e)}", "events": []}

class CreateArgs(BaseModel):
    description: str = Field(..., description="Sentence describing the event, like 'Meeting with Bob tomorrow at 3pm'.")

@tool(args_schema=CreateArgs)
def create_event(*, description: str, user_id: str) -> str:
    """Creates a new Google Calendar event for a user based on a natural language description (e.g., 'Dentist appointment tomorrow at 4pm for 1 hour')."""
    data = find_dates.invoke({"text": description})
    title, date, time = data["title"], data["date"], data["time"]
    dur = int(data.get("duration_minutes", 60))
    service = get_calendar_service(user_id=user_id)

    if time and time != "00:00":
        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").astimezone(CHICAGO_TZ)
        end_dt = start_dt + timedelta(minutes=dur)
        body = {"summary": title, "start": {"dateTime": start_dt.isoformat()}, "end": {"dateTime": end_dt.isoformat()}}
    else:
        body = {"summary": title, "start": {"date": date}, "end": {"date": date}}
    
    service.events().insert(calendarId="primary", body=body).execute()
    return f"Event '{title}' created on {date}{' at '+time if time!='00:00' else ''}"

class RangeArgs(BaseModel):
    request: str = Field(..., description="A natural language date range, like 'next week' or 'June 1-5'.")

@tool(args_schema=RangeArgs)
def get_events_in_range(*, request: str, user_id: str) -> str:
    """Finds and lists all calendar events for a user within a natural language date range (e.g., 'this week', 'next month', 'August 5th to 10th')."""
    try:
        service = get_calendar_service(user_id=user_id)
        prompt = f"""Today is {TODAY}. Extract start_date and end_date (YYYY-MM-DD) from the text: "{request}". Respond ONLY as JSON: {{"start_date":"YYYY-MM-DD","end_date":"YYYY-MM-DD"}}"""
        response_content = get_llm().invoke(prompt).content.strip()
        dates = json.loads(response_content)
        s, e = dates["start_date"], dates["end_date"]
        
        start_dt = datetime.strptime(f"{s} 00:00:00", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)
        end_dt = datetime.strptime(f"{e} 23:59:59", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)

        items = service.events().list(calendarId="primary", timeMin=start_dt.isoformat(), timeMax=end_dt.isoformat(), singleEvents=True, orderBy="startTime").execute().get("items", [])
        
        if not items:
            return f"No events found between {s} and {e}."
        
        event_strings = [f"{it['start'].get('dateTime', it['start'].get('date'))} – {it.get('summary','(No title)')}" for it in items]
        return "Events: " + " | ".join(event_strings)
    except Exception as e:
        return f"Error processing date range '{request}': {str(e)}"

class DeleteArgs(BaseModel):
    instruction: str = Field(..., description="Instruction to delete an event, e.g., \"'Event Title' on YYYY-MM-DD\"")

@tool(args_schema=DeleteArgs)
def delete_event(*, instruction: str, user_id: str) -> str:
    """Deletes a Google Calendar event for a user. The instruction must contain the event's exact title and its date, formatted like: 'Event Title on YYYY-MM-DD'."""
    if " on " not in instruction.lower():
        return "Instruction format error. Please provide as: <title> on YYYY-MM-DD"
    
    parsed_title_part, date_str = instruction.rsplit(" on ", 1)
    final_title = parsed_title_part.strip().strip("'\" ")
    date_str = date_str.strip()

    service = get_calendar_service(user_id=user_id)
    day_start = datetime.strptime(f"{date_str} 00:00:00", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)
    day_end = datetime.strptime(f"{date_str} 23:59:59", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)

    events = service.events().list(calendarId="primary", timeMin=day_start.isoformat(), timeMax=day_end.isoformat(), singleEvents=True).execute().get("items", [])
    event_to_delete = next((ev for ev in events if ev.get("summary", "").lower() == final_title.lower()), None)

    if event_to_delete:
        service.events().delete(calendarId="primary", eventId=event_to_delete["id"]).execute()
        return f"Successfully deleted event: '{event_to_delete.get('summary', final_title)}' on {date_str}."
    else:
        return f"No event found with the exact title '{final_title}' on {date_str} to delete."

@tool
def _parse_date_fallback(request: str) -> dict:
    """Fallback date parsing for common expressions like 'today', 'tomorrow', or 'next week' when the primary date parsing fails."""
    today = datetime.now(CHICAGO_TZ).date()
    request_lower = request.lower()
    start_date, end_date = today, today

    if "tomorrow" in request_lower:
        start_date = end_date = today + timedelta(days=1)
    elif "this week" in request_lower:
        start_date = today - timedelta(days=(today.weekday() + 1) % 7)
        end_date = start_date + timedelta(days=6)
    elif "next week" in request_lower:
        start_of_this_week = today - timedelta(days=(today.weekday() + 1) % 7)
        start_date = start_of_this_week + timedelta(days=7)
        end_date = start_date + timedelta(days=6)

    return {"start_date": start_date.strftime('%Y-%m-%d'), "end_date": end_date.strftime('%Y-%m-%d')}