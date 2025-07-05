import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from langchain.tools import tool
from pydantic import BaseModel, Field
from lc.config import get_llm

# Import the Google Calendar service getter directly
from core.google_auth import get_calendar_service
from googleapiclient.errors import HttpError

# --- Pydantic Models for Tool Inputs ---

class CreateReminderInput(BaseModel):
    """Input model for the create_reminder_tool."""
    title: str = Field(description="The title or subject of the reminder.")
    remind_at_str: str = Field(description="The date and time for the reminder in natural language (e.g., 'tomorrow at 5pm', 'June 28th at 10am').")

class DeleteReminderInput(BaseModel):
    """Input model for the delete_reminder_tool."""
    title: str = Field(description="The exact title of the reminder to be deleted.")

class CheckReminderInput(BaseModel):
    """Input model for the check_reminder_exists tool."""
    title: str = Field(description="The title of the reminder to check for.")

# --- Reminder Creation Tool ---

@tool("create_reminder_tool", args_schema=CreateReminderInput)
def create_reminder_tool(title: str, remind_at_str: str) -> str:
    """
    Creates a reminder for the user. It intelligently parses a natural language
    date and time, saves the reminder, and adds it as an event to the user's
    Google Calendar. Use this when a user asks to be reminded of something.
    """
    print(f"--- TOOL: Running create_reminder_tool for: {title} ---")
    
    try:
        # Step 1: Use an LLM to parse the natural language date/time into ISO format.
        llm = get_llm()
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        parser_prompt = f"""
        Given the current date and time is {current_time_str}, convert the following
        natural language request into a single, precise ISO 8601 timestamp string
        (YYYY-MM-DDTHH:MM:SS). Respond with ONLY the timestamp string.

        Request: "{remind_at_str}"
        """
        
        parsed_time_str = llm.invoke(parser_prompt).content.strip()
        remind_at_dt = datetime.fromisoformat(parsed_time_str)
        print(f"--- LLM parsed '{remind_at_str}' to '{remind_at_dt.isoformat()}' ---")

        # Step 2: Save the reminder to the local reminders.json file
        reminders_db_file = "reminders.json"
        try:
            with open(reminders_db_file, 'r') as f:
                reminders = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            reminders = []
            
        new_reminder = {
            "id": str(uuid.uuid4()),
            "title": title,
            "remind_at": remind_at_dt.isoformat(),
            "status": "Pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Step 3: Add the corresponding event to Google Calendar
        print(f"--- Adding reminder to Google Calendar... ---")
        calendar_service = get_calendar_service()
        event_body = {
            'summary': f"Reminder: {title}",
            'start': {'dateTime': remind_at_dt.isoformat(), 'timeZone': 'America/Chicago'},
            'end': {'dateTime': (remind_at_dt + timedelta(minutes=30)).isoformat(), 'timeZone': 'America/Chicago'},
            'reminders': {'useDefault': True},
        }
        created_event = calendar_service.events().insert(calendarId='primary', body=event_body).execute()
        
        # Add the event ID to our local reminder object for future reference
        new_reminder['google_calendar_event_id'] = created_event.get('id')
        
        reminders.append(new_reminder)
        with open(reminders_db_file, 'w') as f:
            json.dump(reminders, f, indent=4)
        
        return f"OK. I've scheduled a reminder for '{title}' on {remind_at_dt.strftime('%A, %B %d at %I:%M %p')} and added it to your calendar."

    except Exception as e:
        print(f"--- ERROR in create_reminder_tool: {e} ---")
        return f"An unexpected error occurred while creating the reminder: {str(e)}"

# --- Reminder Deletion Tool ---

@tool("delete_reminder_tool", args_schema=DeleteReminderInput)
def delete_reminder_tool(title: str) -> str:
    """
    Deletes a reminder from the user's list based on its exact title.
    It also attempts to delete the corresponding event from Google Calendar.
    Use this when a user asks to delete or remove a reminder.
    """
    print(f"--- TOOL: Running delete_reminder_tool for: {title} ---")
    
    reminders_db_file = "reminders.json"
    try:
        with open(reminders_db_file, 'r') as f:
            reminders = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "Error: Could not find the reminders list."

    # Find the reminder to delete
    reminder_to_delete = None
    for reminder in reminders:
        if reminder.get("title", "").lower() == title.lower():
            reminder_to_delete = reminder
            break

    if not reminder_to_delete:
        return f"Error: Could not find a reminder named '{title}'."

    # If the reminder has a linked calendar event, try to delete it
    event_id = reminder_to_delete.get("google_calendar_event_id")
    if event_id:
        try:
            print(f"--- Deleting Google Calendar event: {event_id} ---")
            calendar_service = get_calendar_service()
            calendar_service.events().delete(calendarId='primary', eventId=event_id).execute()
            print("--- Google Calendar event deleted successfully. ---")
        except HttpError as e:
            if e.resp.status in [404, 410]:
                 print(f"--- INFO: Calendar event already gone. ---")
            else:
                print(f"--- WARNING: Could not delete Google Calendar event. {e} ---")
        except Exception as e:
            print(f"--- WARNING: An unexpected error occurred while deleting calendar event. {e} ---")

    # Remove the reminder from the local list and save
    reminders.remove(reminder_to_delete)
    with open(reminders_db_file, 'w') as f:
        json.dump(reminders, f, indent=4)

    return f"Successfully deleted reminder: '{title}'."

# --- Reminder Check Tool ---

@tool("check_reminder_exists", args_schema=CheckReminderInput)
def check_reminder_exists(title: str) -> str:
    """
    Checks if a reminder with a specific title already exists in the user's list.
    Returns a confirmation message with the scheduled time if found, or a "not found" message.
    """
    print(f"--- TOOL: Running check_reminder_exists for: {title} ---")
    
    reminders_db_file = "reminders.json"
    try:
        with open(reminders_db_file, 'r') as f:
            reminders = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "Could not access the reminders list."

    # Search for the reminder (case-insensitive)
    found_reminder = None
    for reminder in reminders:
        if reminder.get("title", "").lower() == title.lower():
            found_reminder = reminder
            break

    if found_reminder:
        remind_at_dt = datetime.fromisoformat(found_reminder['remind_at'])
        formatted_time = remind_at_dt.strftime('%A, %B %d at %I:%M %p')
        return f"Yes, you have a reminder for '{title}' scheduled for {formatted_time}."
    else:
        return f"No, you do not have a reminder set for '{title}'."

# --- Tool to List All Reminders (Updated) ---

@tool
def list_all_reminders() -> List[Dict]:
    """
    Lists all upcoming reminders from the user's list. Returns a list of dictionaries,
    each containing a reminder's title and its scheduled time. Use this when the user
    asks a general question like 'what are my reminders?' or 'show me my reminders'.
    """
    print(f"--- TOOL: Running list_all_reminders ---")
    
    reminders_db_file = "reminders.json"
    try:
        with open(reminders_db_file, 'r') as f:
            reminders = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return an empty list if there are no reminders
        return []

    if not reminders:
        return []

    # Sort reminders by date
    reminders.sort(key=lambda r: r.get('remind_at', ''))
    
    # Format the list into a list of dictionaries for structured output
    formatted_list = []
    for reminder in reminders:
        remind_at_dt = datetime.fromisoformat(reminder['remind_at'])
        formatted_list.append({
            "title": reminder['title'],
            "remind_at": remind_at_dt.strftime('%b %d at %I:%M %p')
        })
        
    # Return the structured list
    return formatted_list
