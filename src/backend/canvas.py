# canvas.py
from canvasapi import Canvas
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()
API_URL = "https://unt.instructure.com"
API_KEY = os.getenv("CANVAS_API_KEY")

canvas = Canvas(API_URL, API_KEY)

def get_current_courses():
    return [c for c in canvas.get_courses() if getattr(c, 'name', None) and not c.name.startswith("CSCE 1")]

def get_upcoming_assignments():
    now = datetime.now(timezone.utc)
    upcoming = []
    for course in get_current_courses():
        try:
            for a in list(course.get_assignments()):
                if a.due_at:
                    due = datetime.fromisoformat(a.due_at.replace("Z", "+00:00"))
                    if due > now:
                        upcoming.append({"course": course.name, "assignment": a.name, "due": due})
        except Exception as e:
            print(f"❌ {course.name}: {e}")
    return upcoming

def format_assignments(assignments):
    if not assignments:
        return "🎉 No upcoming assignments."
    return "\n".join([f"📘 {a['course']} — 📝 {a['assignment']} due on {a['due'].strftime('%b %d, %I:%M %p')}" for a in assignments])

def get_grades():
    grades = []
    for course in get_current_courses():
        try:
            grade = course.get_enrollments()[0].grades.get("current_score")
            grades.append(f"📗 {course.name}: {grade or 'N/A'}")
        except Exception as e:
            print(f"❌ {course.name}: {e}")
    return "\n".join(grades) if grades else "No grades available."

def get_course_list():
    courses = get_current_courses()
    return "📘 Your courses:\n" + "\n".join(f"- {c.name}" for c in courses)

def get_calendar_service():
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

def sync_assignments_to_google_calendar():
    service = get_calendar_service()
    assignments = get_upcoming_assignments()
    if not assignments:
        return "🎉 No assignments to sync."
    count = 0
    for a in assignments:
        event = {
            "summary": f"{a['course']} - {a['assignment']}",
            "description": "Canvas Assignment",
            "start": {"dateTime": a['due'].isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": (a['due'] + timedelta(hours=1)).isoformat(), "timeZone": "UTC"},
            "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 60}]}
        }
        try:
            service.events().insert(calendarId="primary", body=event).execute()
            count += 1
        except Exception as e:
            print(f"❌ {a['assignment']}: {e}")
    return f"✅ Synced {count} assignment(s) to calendar."
