import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, field_validator
from langchain_core.tools import tool
from lc.config import get_llm
from core.google_auth import get_calendar_service
import asyncio                    # ← NEW


CHICAGO_TZ = ZoneInfo("America/Chicago")
TODAY = datetime.now(CHICAGO_TZ).strftime("%Y-%m-%d")

def _to_future(date_obj: datetime.date) -> datetime.date:
    """If *date_obj* is in the past, move it to the same month/day next year."""
    today = datetime.now(CHICAGO_TZ).date()
    if date_obj < today:
        return date_obj.replace(year=date_obj.year + 1)
    return date_obj

def get_all_events(user_id: str, max_results: int = 250) -> list: 

     """Fetches all upcoming calendar events for *user_id*.""" 
     now = datetime.now(CHICAGO_TZ).isoformat()-8000 
     service = asyncio.run(get_calendar_service(user_id))   
     events_result = service.events().list( 
         calendarId="primary", timeMin=now, maxResults=max_results, 
         singleEvents=True, orderBy="startTime" 
     ).execute() 

     return events_result.get("items", [])

class FindDatesArgs(BaseModel):
    text: str = Field(..., description="Free‑text with a date expression, like 'meeting tomorrow at 3pm'")

@tool(args_schema=FindDatesArgs)
def find_dates(text: str) -> str:
    """Parses a natural language string containing date/time info into a structured JSON string."""
    prompt = f"""You are a date‑parsing expert. Extract a *future* date, title, time, and (optional) duration.
Today is {TODAY}. If the user omits a year (e.g. "August 8th"), assume the *next* occurrence in the future.
The output MUST be valid JSON exactly in this schema: {{"title":"","date":"YYYY-MM-DD","time":"HH:MM","duration_minutes":60}}.
USER SENTENCE: "{text}"
"""
    raw = get_llm().invoke(prompt).content.strip()
    data = json.loads(raw)
    parsed_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    data["date"] = _to_future(parsed_date).isoformat()
    # FIX: Return a proper JSON string to ensure agent stability
    return json.dumps(data)

@tool
def get_current_date() -> str:
    """Gets the current date in YYYY-MM-DD format for the America/Chicago timezone."""
    return datetime.now(CHICAGO_TZ).strftime("%Y-%m-%d")

DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"

class EventsOnArgs(BaseModel):
    date: str = Field(
        ...,
        pattern=DATE_PATTERN,
        description="Date in YYYY‑MM‑DD format. The 'find_dates' tool must be used first for natural language dates.",
    )

    @field_validator("date", mode='before')
    def future_bias(cls, v: str) -> str:
        """Ensures the provided date is in the future."""
        dt = datetime.strptime(v, "%Y-%m-%d").date()
        return _to_future(dt).isoformat()

@tool(args_schema=EventsOnArgs)
def get_events_on_date(*, date: str, user_id: str) -> dict:
    """Returns a list of all calendar events for a user on a given date."""
    service = asyncio.run(get_calendar_service(user_id)) 
    day_start = datetime.strptime(f"{date} 00:00:00", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)
    day_end = datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S").astimezone(CHICAGO_TZ)
    items = service.events().list(
        calendarId="primary", timeMin=day_start.isoformat(), timeMax=day_end.isoformat(),
        singleEvents=True, orderBy="startTime"
    ).execute().get("items", [])

    if not items:
        return {"status": f"You’re free on {date}", "events": []}

    simplified = [{"summary": e.get("summary", "(No title)"), "start": e.get("start"), "end": e.get("end"), "id": e.get("id")} for e in items]
    return {"status": f"Found {len(simplified)} events on {date}.", "events": simplified}

class CreateArgs(BaseModel):
    description: str = Field(..., description="A natural language description of an event, e.g. 'Dentist tomorrow at 4pm for 1 hour'.")

@tool(args_schema=CreateArgs)
def create_event(*, description: str, user_id: str) -> str:
    """Creates a new Google Calendar event from a natural language description."""
    # FIX: Parse the JSON string that the find_dates tool now returns
    data_string = find_dates.invoke({"text": description})
    data = json.loads(data_string)

    title, date_str, time_str = data["title"], data["date"], data["time"]
    dur = int(data.get("duration_minutes", 60))
    service = asyncio.run(get_calendar_service(user_id)) 

    if time_str and time_str != "00:00":
        start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").astimezone(CHICAGO_TZ)
        end_dt = start_dt + timedelta(minutes=dur)
        body = {"summary": title, "start": {"dateTime": start_dt.isoformat()}, "end": {"dateTime": end_dt.isoformat()}}
    else:
        body = {"summary": title, "start": {"date": date_str}, "end": {"date": date_str}}

    service.events().insert(calendarId="primary", body=body).execute()
    return f"Event '{title}' created on {date_str}{' at '+time_str if time_str!='00:00' else ''}."

# ... (rest of tools: get_events_in_range, delete_event, _parse_date_fallback)

class RangeArgs(BaseModel):
    request: str = Field(..., description="A natural language date range, like 'next week' or 'June 1-5'.")

@tool(args_schema=RangeArgs)
def get_events_in_range(*, request: str, user_id: str) -> str:
    """Finds and lists all calendar events for a user within a natural language date range (e.g., 'this week', 'next month', 'August 5th to 10th')."""
    try:
        service = asyncio.run(get_calendar_service(user_id)) 
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

    service = asyncio.run(get_calendar_service(user_id)) 
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
