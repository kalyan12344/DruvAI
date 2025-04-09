# calendar.py
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES, redirect_uri='http://localhost:5000')
            creds = flow.run_local_server(port=5000)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        return build('calendar', 'v3', credentials=creds)

    def create_event(self, title, start_time, duration_minutes=60, description=""):
        end_time = start_time + timedelta(minutes=duration_minutes)
        event = {
            "summary": title,
            "description": description or "Scheduled via Druv",
            "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 60 * 24},
                    {"method": "popup", "minutes": 30}
                ]
            }
        }
        self.service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ Event '{title}' created on Google Calendar."
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
