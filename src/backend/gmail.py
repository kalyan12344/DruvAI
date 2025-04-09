from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# 🔐 Groq API setup
groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailService:
    def __init__(self):
        creds = None
        if os.path.exists('gmail_token.json'):
            creds = Credentials.from_authorized_user_file('gmail_token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('gmail_token.json', 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        self.important_emails = []

    def is_important_with_llm(self, subject, sender, snippet):
        prompt = f"""
You are an email assistant. Based on the subject and content, decide if this email is important. Only respond with 'Yes' or 'No'.

Subject: {subject}
Sender: {sender}
Content: {snippet}
"""

        try:
            response = groq_client.chat.completions.create(
                model="gemma2-9b-it",  # or llama3-70b-8192
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that decides if emails are important."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            answer = response.choices[0].message.content
            return "yes" in answer.lower()
        except Exception as e:
            print("⚠️ LLM error:", e)
            return False

    def get_unread_emails(self, max_results=5):
        try:
            result = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                q='is:unread newer_than:2d',
                maxResults=max_results
            ).execute()

            total_unread = result.get("resultSizeEstimate", 0)
            messages = result.get('messages', [])
            self.important_emails = []
            print(messages)

            if not messages:
                return ["📭 You have no unread emails in the last 2 days."]

            for msg in messages:
                msg_data = self.service.users().messages().get(userId='me', id=msg['id']).execute()
                headers = msg_data['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
                sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown Sender")
                snippet = msg_data.get('snippet', '')

                formatted_email = f"📨 *{subject}* from *{sender}*\n{snippet}"

                if self.is_important_with_llm(subject, sender, snippet):
                    formatted_email = f"⭐️ {formatted_email}"
                    print("⭐️ Important email found:", formatted_email)
                    self.important_emails.append(formatted_email)

            if total_unread > max_results:
                self.important_emails.append(
                    f"\n📌 You have {total_unread} unread emails. Showing top {max_results} scanned for importance."
                )

            return self.important_emails or ["📭 No important emails found."]

        except Exception as e:
            print("❌ Gmail error:", e)
            return ["❌ Failed to fetch emails."]

    def get_important_emails(self):
        return self.important_emails


# ✅ Shared instance used in both background and Flask app
# gmail_service_instance = GmailService()

# def start_periodic_check(interval_minutes=2, max_results=5):
#     print("🔄 Starting periodic email check...")
#     print(f"📡 Started watching for important emails every {interval_minutes} minutes...\n")

#     while True:
#         print("🔍 Checking for important emails...")
#         important_emails = gmail_service_instance.get_unread_emails(max_results=max_results)

#         print("✅ Important emails found:")
#         for msg in important_emails:
#             print(msg)

#         print("⏳ Sleeping for", interval_minutes, "minutes...\n")
#         time.sleep(interval_minutes * 60)


# if __name__ == "__main__":
#     start_periodic_check(interval_minutes=1)
