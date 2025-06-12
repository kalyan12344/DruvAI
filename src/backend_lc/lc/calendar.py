#lc/calendar.py

"""
Google-Calendar utilities exposed as LangChain tools.
Relies on core.google_auth.get_calendar_service() already in your codebase.
"""
import json
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from lc.config import get_llm
from core.google_auth import get_calendar_service
import re

TODAY = datetime.utcnow().strftime("%Y-%m-%d")

# ─────────── helper ────────────────────────────────────────────
def _svc():
    return get_calendar_service()

def get_all_events(max_results: int = 250) -> list:
    """
    Fetches all upcoming calendar events as a standard Python function.
    
    Args:
        max_results (int): The maximum number of events to return.
        
    Returns:
        list: A list of event dictionaries from the Google Calendar API.
    """
    print(f"Fetching up to {max_results} upcoming events...")
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    
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

    Example: "Dentist appointment on next Friday at 3pm for 30 minutes"
    Returns {title,date,time,duration_minutes}.

    If no time is specified, assume 00:00 (midnight).

    If no duration is specified, assume 60 minutes.

    Make sure the title is from the description
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
    Get the current date in YYYY-MM-DD format.
    Use this tool when the user asks for today's date or current date.
    """
    return datetime.now().strftime("%Y-%m-%d")
# ─────────── get_events_on_date ────────────────────────────────
class EventsOnArgs(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")

@tool(args_schema=EventsOnArgs)
def get_events_on_date(date: str) -> str:

    """
    today is {TODAY}
    if dates are not specified example if said next week first call find_dates and then get the date accordingly
    Return a friendly list of all events on *date* . today is {TODAY}. always refer to this date and then look for the date accordingly 
     very important if year is not specified, assume current year.
        For natural language dates (e.g., 'tomorrow', 'next Friday'), you MUST use the 'find_dates' tool FIRST to convert them to YYYY-MM-DD format.

    """
    start, end = f"{date}T00:00:00Z", f"{date}T23:59:59Z"
    items = _svc().events().list(calendarId="primary",
                                 timeMin=start, timeMax=end,
                                 singleEvents=True, orderBy="startTime"
                                 ).execute().get("items", [])
    if not items:
        return f"🎉 You’re free on {date}"
    return  " | ".join(
        f"{e['start'].get('dateTime', e['start'].get('date'))} – {e.get('summary','(No title)')}"
        for e in items
    )

# ─────────── get_events_in_range ───────────────────────────────
class RangeArgs(BaseModel):
    request: str = Field(..., description="Sentence like 'next week' or 'June 1-5'")

@tool(args_schema=RangeArgs)
def get_events_in_range(request: str) -> str:
    """Interpret a natural date range and list events inside it."""
    try:
        prompt = f"""Today is {TODAY}.
Extract start_date and end_date (YYYY-MM-DD) from the text below.

"{request}"

Respond as:
{{"start_date":"YYYY-MM-DD","end_date":"YYYY-MM-DD"}}
"""
        
        # Get LLM response and handle potential issues
        llm_response = get_llm().invoke(prompt)
        response_content = llm_response.content.strip()
        
        # Debug: print what LLM returned
        print(f"LLM Response for '{request}': '{response_content}'")
        
        # Check if response is empty
        if not response_content:
            raise ValueError("LLM returned empty response")
        
        # Try to parse JSON with better error handling
        try:
            dates = json.loads(response_content)
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"Raw response: '{response_content}'")
            
            # Try to extract JSON from response if it's wrapped in other text
            import re
            json_match = re.search(r'\{[^{}]*"start_date"[^{}]*"end_date"[^{}]*\}', response_content)
            if json_match:
                json_str = json_match.group(0)
                print(f"Extracted JSON: '{json_str}'")
                dates = json.loads(json_str)
            else:
                # Fallback: parse common date expressions manually
                dates = _parse_date_fallback(request)
        
        # Validate the parsed dates
        if not isinstance(dates, dict) or 'start_date' not in dates or 'end_date' not in dates:
            raise ValueError("Invalid date format returned by LLM")
        
        s, e = dates["start_date"], dates["end_date"]
        
        # Validate date format
        from datetime import datetime
        try:
            datetime.strptime(s, '%Y-%m-%d')
            datetime.strptime(e, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Invalid date format: start_date={s}, end_date={e}")
        
        # Get calendar events
        items = _svc().events().list(calendarId="primary",
                                     timeMin=f"{s}T00:00:00Z",
                                     timeMax=f"{e}T23:59:59Z",
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
    from datetime import datetime, timedelta
    
    today = datetime.now()
    request_lower = request.lower()
    
    if "next week" in request_lower:
        # Next Monday to Sunday
        days_until_monday = 7 - today.weekday()
        start = today + timedelta(days=days_until_monday)
        end = start + timedelta(days=6)
    elif "this week" in request_lower:
        # This Monday to Sunday
        days_since_monday = today.weekday()
        start = today - timedelta(days=days_since_monday)
        end = start + timedelta(days=6)
    elif "tomorrow" in request_lower:
        start = end = today + timedelta(days=1)
    elif "today" in request_lower:
        start = end = today
    elif "next month" in request_lower:
        if today.month == 12:
            start = datetime(today.year + 1, 1, 1)
            end = datetime(today.year + 1, 1, 31)
        else:
            start = datetime(today.year, today.month + 1, 1)
            # Last day of next month
            if today.month + 1 == 12:
                end = datetime(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end = datetime(today.year, today.month + 2, 1) - timedelta(days=1)
    else:
        # Default to next 7 days
        start = today
        end = today + timedelta(days=7)
    
    return {
        "start_date": start.strftime('%Y-%m-%d'),
        "end_date": end.strftime('%Y-%m-%d')
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
        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        end_dt   = start_dt + timedelta(minutes=dur)
        body = {
            "summary": title,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "America/Chicago"},
            "end":   {"dateTime": end_dt.isoformat(),   "timeZone": "America/Chicago"},
        }
    else:  # all-day
        body = {
            "summary": title,
            "start": {"date": date},
            "end":   {"date": date},
        }
    svc.events().insert(calendarId="primary", body=body).execute()
    return f"✅ '{title}' created on {date}{' '+time if time!='00:00' else ''}"

# ─────────── delete_event ──────────────────────────────────────
class DeleteArgs(BaseModel):
    instruction: str = Field(..., 
                             description="Instruction to delete an event. "
                                         "Ideally, format as: \"'Exact Event Title' on YYYY-MM-DD\". "
                                         "For example: \"'Dentist Appointment' on 2025-05-20\". "
                                         "The tool will attempt to clean common command words if they are included, "
                                         "but providing just the title and date is best.")

@tool(args_schema=DeleteArgs)
def delete_event(instruction: str) -> str:
    """
    Delete an event by its exact title and date.
    Parses an instruction like "'Event Title' on YYYY-MM-DD" or "Delete 'Event Title' on YYYY-MM-DD".
    """
    if " on " not in instruction.lower():
        return "⚠️ Instruction format error. Please provide as: <title> on YYYY-MM-DD"
    
    try:
        parsed_title_part, date_str = instruction.rsplit(" on ", 1)
    except ValueError:
        return "⚠️ Instruction format error. Could not properly separate title and date using ' on '."

    date_str = date_str.strip()
    temp_title = parsed_title_part.strip()

    command_patterns = [
        re.compile(r"^(delete|remove|cancel)\s+", flags=re.IGNORECASE),
    ]

    for pattern in command_patterns:
        temp_title = pattern.sub("", temp_title, count=1)
    
    final_title = temp_title.strip("'\" ")

    if not final_title:
        return "❌ Error: Event title appears to be empty after parsing the instruction."
    if not date_str:
        return "❌ Error: Date appears to be empty after parsing."

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return (f"⚠️ Error: The extracted date '{date_str}' is not in YYYY-MM-DD format. "
                f"Please ensure the date is specified correctly.")

    start_utc = f"{date_str}T00:00:00Z"
    end_utc = f"{date_str}T23:59:59Z"

    svc = _svc()
    try:
        events_response = svc.events().list(
            calendarId="primary",
            timeMin=start_utc,
            timeMax=end_utc,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
    except Exception as e:
        return f"❌ Error fetching events for {date_str} to find the event for deletion: {str(e)}"
        
    events = events_response.get("items", [])

    if not events:
        return f"ℹ️ No events found on {date_str} at all, so '{final_title}' could not be deleted."

    event_found_to_delete = None
    for ev in events:
        event_summary = ev.get("summary", "")
        if final_title.lower() == event_summary.lower():
            event_found_to_delete = ev
            break
    
    if event_found_to_delete:
        try:
            svc.events().delete(calendarId="primary", eventId=event_found_to_delete["id"]).execute()
            return f"🗑️ Successfully deleted event: '{event_found_to_delete.get('summary', final_title)}' on {date_str}."
        except Exception as e:
            return f"❌ Error trying to delete event '{event_found_to_delete.get('summary', final_title)}' (ID: {event_found_to_delete.get('id')}): {str(e)}"
    else:
        return f"❌ No event found with the exact title '{final_title}' on {date_str} to delete."
