# calendar.py
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pytesseract
from PIL import Image
import io
from datetime import datetime, timedelta


SCOPES = ['https://www.googleapis.com/auth/calendar']

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'calender_token.json'

class CalendarService:
    def __init__(self):
        print("Initializing Google Calendar Service...")
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None
        if os.path.exists(TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                creds = None  # prevent infinite recursion


        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES, redirect_uri='http://localhost:5001')
            creds = flow.run_local_server(port=5001)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        return build('calendar', 'v3', credentials=creds)

    def create_event(self, title, start_time, duration_minutes=60, description=""):
        print("Creating event...", title)
        print("Start time:", start_time)
        """
        Creates an event on Google Calendar.

        If start_time is a datetime → normal timed event.
        If start_time is a date string (YYYY-MM-DD) → all-day event.
        """
        # Handle all-day event if only a date is given
        if isinstance(start_time, str):
            try:
                date = datetime.strptime(start_time, "%Y-%m-%d").date()
                event = {
                    "summary": title,
                    "description": description or "Scheduled via Druv",
                    "start": {"date": str(date)},
                    "end": {"date": str(date + timedelta(days=1))},
                    "reminders": {
                        "useDefault": False,
                        "overrides": [
                            {"method": "email", "minutes": 60 * 24},  # 1 day before
                            {"method": "popup", "minutes": 30}
                        ]
                    }
                }
                self.service.events().insert(calendarId='primary', body=event).execute()
                return f"✅ All-day event '{title}' created for {date}."
            except Exception as e:
                return f"❌ Failed to create all-day event: {e}"

        # Else, treat it as a timed event
        try:
            end_time = start_time + timedelta(minutes=duration_minutes)
            event = {
            "summary": title,
            "description": description or "Scheduled via Druv",
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "America/Chicago"
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "America/Chicago"
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 60 * 24},
                    {"method": "popup", "minutes": 30}
                ]
            }
        }

            self.service.events().insert(calendarId='primary', body=event).execute()
            return f"✅ Timed event '{title}' created on {start_time.strftime('%Y-%m-%d %H:%M')}."
        except Exception as e:
            return f"❌ Failed to create timed event: {e}"

    def get_event_by_date(self, date_str):
        """
        Fetch events on a specific date (YYYY-MM-DD).
        """
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            start = date.isoformat() + 'Z'
            end = (date + timedelta(days=1)).isoformat() + 'Z'

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            return events_result.get('items', [])
        except Exception as e:
            print(f"Error in get_event_by_date: {e}")
            return []

    def get_events(self, count=5):
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(
            calendarId='primary', timeMin=now, maxResults=count, singleEvents=True, orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

    def get_all_events(self, max_results=250):
        print("Fetching all events...")
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(
            calendarId='primary', timeMin=now, maxResults=max_results, singleEvents=True, orderBy='startTime'
        ).execute()
        print("Events fetched successfully.")
        return events_result.get('items', [])

    def get_event_by_range(self, start_date_str, end_date_str):
        start = datetime.strptime(start_date_str, "%Y-%m-%d").isoformat() + 'Z'
        end = (datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1)).isoformat() + 'Z'
        events_result = self.service.events().list(
            calendarId='primary', timeMin=start, timeMax=end, singleEvents=True, orderBy='startTime'
        ).execute()
        return events_result.get('items', [])


def extract_text_from_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(image)
def extract_kalyan_shifts(text):
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for line in text.splitlines():
        if line.strip().lower().startswith("kalyan"):
            parts = line.split()
            shift_values = parts[1:]

            # Determine start day (e.g., if only 5 shifts are present starting from Wed)
            start_index = 0
            if len(shift_values) < 7:
                # Heuristic: Assume starts from current weekday (e.g., Wed)
                today = datetime.today().weekday()  # Monday = 0
                start_index = 2  # If Wed is your usual start day → index 2

            aligned_days = days[start_index:start_index + len(shift_values)]

            return dict(zip(aligned_days, shift_values))
    return {}

def get_kalyan_shift_schedule_from_image(image_bytes):
    text = extract_text_from_image(image_bytes)
    shifts = extract_kalyan_shifts(text)

    # Map weekdays to index
    day_to_index = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

    # Get the Monday of the current week
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday

    shift_schedule = []
    for day, time_range in shifts.items():
        if time_range.strip().lower() in ["", "off"]:
            continue
        day_index = day_to_index[day]
        shift_date = start_of_week + timedelta(days=day_index)
        shift_schedule.append({
            "day": day,
            "date": shift_date.strftime("%Y-%m-%d"),
            "time_range": time_range
        })
    # print("Shift schedule extracted:", shift_schedule)
    return shift_schedule

