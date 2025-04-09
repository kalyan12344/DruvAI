from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from calender import CalendarService
from canvas import (
    get_upcoming_assignments,
    format_assignments,
    get_grades,
    get_current_courses,
    get_course_list,
    sync_assignments_to_google_calendar,
)
from websearch import (web_search)
import os
import requests
from dotenv import load_dotenv
import json
import re
from gmail import GmailService
gmail_service = GmailService()
import threading
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

# Setup the client using Groq base
groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


# from hotword import start_hotword_thread

# def on_wake_word_detected():
    # print("🔔 Druv is listening now...")
    # You can trigger your voice recognition or UI update here

# start_hotword_thread(on_wake_word_detected)


# --------------------- Setup ---------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5176"]}})
load_dotenv()
calendar_service = CalendarService()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# --------------------- Supported Intents ---------------------
SUPPORTED_INTENTS = [
    "create_event",
    "get_event",
    "get_all_events",
    "get_event_by_range",
    "get_time",
    "get_event_by_date",
    "get_current_courses",
    "get_course_list",
    "get_upcoming_assignments",
    "get_grades",
    "sync_assignments_to_google_calendar",
    "chat",
    "get_unread_emails",
]

# --------------------- LLM Intent Extractor ---------------------

def call_llm(prompt):
    today_str = datetime.today().strftime("%A, %B %d, %Y")

    function_guide = f"""
Today’s date is {today_str}.

You are Druv's intent engine. You must understand the user's command and respond with the correct intent and required arguments.

If a tool is required use the tool_calls.
If a tool is not required respond normally.

Only use one of the following intents (DO NOT invent new ones):

1. create_event
   → args: {{ "title": str, "date": "YYYY-MM-DD", "time": "HH:MM" }}

2. get_event
   → args: {{ }}

3. get_all_events
   → args: {{ }}

4. get_event_by_date
   → args: {{ "date": "YYYY-MM-DD" }}

5. get_event_by_range
   → args: {{ "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }}

7. get_current_courses
   → args: {{ }}

8. get_course_list
   → args: {{ }}

9. get_upcoming_assignments
   → args: {{ }}

10. get_grades
    → args: {{ }}

11. sync_assignments_to_google_calendar
    → args: {{ }}

12. chat  
→ args: {{ "message": str }}  
Use this when the user is asking general questions, chatting, making fun/non-functional requests, or requesting general knowledge, news, or trending information.

🧠 If the user asks something factual, trending, or general-knowledge-based (e.g., “What is quantum computing?”, “Latest news in Hyderabad”, “Who is Elon Musk?”), respond with:

→ {{ "intent": "chat", "arguments": {{ "message": "search: user’s question" }} }}

✅ If the user is simply chatting (fun/personal), respond normally.

✨ Always make Druv helpful, polite, friendly, and human-like in tone.

---

Examples:

User: "How are you?"  
→ Response: {{ "intent": "chat", "arguments": {{ "message": "I'm doing great, thanks for asking! 😊 How can I help you today?" }} }}

User: "Tell me a joke"  
→ Response: {{ "intent": "chat", "arguments": {{ "message": "Why did the developer go broke? Because he used up all his cache." }} }}

User: "What's your name?"  
→ Response: {{ "intent": "chat", "arguments": {{ "message": "My name is Druv! I'm your AI assistant, always ready to help 🚀" }} }}

User: "What day is it?"  
→ Response: {{ "intent": "chat", "arguments": {{ "message": "Today is {today_str}." }} }}

User: "What is quantum computing?"  
→ Response: {{ "intent": "chat", "arguments": {{ "message": "search: What is quantum computing?" }} }}

User: "Latest news in Hyderabad"  
→ Response: {{ "intent": "chat", "arguments": {{ "message": "search: Latest news in Hyderabad" }} }}

User: "Who is the CEO of Tesla?"  
→ Response: {{ "intent": "chat", "arguments": {{ "message": "search: CEO of Tesla" }} }}

---

💬 Examples for other intents (DO NOT use chat intent):

User: "Schedule team sync on April 5 at 3 PM"  
→ Response: {{ "intent": "create_event", "arguments": {{ "title": "team sync", "date": "2024-04-05", "time": "15:00" }} }}

User: "What courses am I taking?"  
→ Response: {{ "intent": "get_current_courses", "arguments": {{ }} }}

User: "Show all my events"  
→ Response: {{ "intent": "get_all_events", "arguments": {{ }} }}

13. get_unread_emails  
→ args: { {}}  
Use this when the user says: "Check my emails", "Do I have unread emails?", "Show latest emails", etc.
✅ Always reply with ONLY valid JSON (no markdown or extra text).

"""

    try:
        response = groq_client.chat.completions.create(
            model="gemma2-9b-it",  # Fast + free on Groq!
            messages=[
                { "role": "system", "content": function_guide },
                { "role": "user", "content": prompt }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("LLM Error:", e)
        return json.dumps({
            "intent": "chat",
            "arguments": {"message": "⚠️ Sorry, I'm having trouble with the AI brain right now."}
        })
# def call_llm(prompt):
#     headers = {
#         "Authorization": f"Bearer {OPENROUTER_API_KEY}",
#         "Content-Type": "application/json",
#     }
#     today_str = datetime.today().strftime("%A, %B %d, %Y")
#     # print("Today's date:", today_str)

#     function_guide = f"""
# Today’s date is {today_str}.

# You are Druv's intent engine. You must understand the user's command and respond with the correct intent and required arguments.

# If a tool is required use the tool_calls.
# If a tool is not required respond normally.

# Only use one of the following intents (DO NOT invent new ones):

# 1. create_event
#    → args: {{ "title": str, "date": "YYYY-MM-DD", "time": "HH:MM" }}

# 2. get_event
#    → args: {{ }}

# 3. get_all_events
#    → args: {{ }}

# 4. get_event_by_date
#    → args: {{ "date": "YYYY-MM-DD" }}

# 5. get_event_by_range
#    → args: {{ "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD" }}

# 7. get_current_courses
#    → args: {{ }}

# 8. get_course_list
#    → args: {{ }}

# 9. get_upcoming_assignments
#    → args: {{ }}

# 10. get_grades
#     → args: {{ }}

# 11. sync_assignments_to_google_calendar
#     → args: {{ }}

# 12. chat  
# → args: {{ "message": str }}  
# Use this when the user is asking general questions, chatting, making fun/non-functional requests, or requesting general knowledge, news, or trending information.

# 🧠 If the user asks something factual, trending, or general-knowledge-based (e.g., “What is quantum computing?”, “Latest news in Hyderabad”, “Who is Elon Musk?”), respond with:

# → {{ "intent": "chat", "arguments": {{ "message": "search: user’s question" }} }}

# ✅ If the user is simply chatting (fun/personal), respond normally.

# ✨ Always make Druv helpful, polite, friendly, and human-like in tone.

# ---

# Examples:

# User: "How are you?"  
# → Response: {{ "intent": "chat", "arguments": {{ "message": "I'm doing great, thanks for asking! 😊 How can I help you today?" }} }}

# User: "Tell me a joke"  
# → Response: {{ "intent": "chat", "arguments": {{ "message": "Why did the developer go broke? Because he used up all his cache." }} }}

# User: "What's your name?"  
# → Response: {{ "intent": "chat", "arguments": {{ "message": "My name is Druv! I'm your AI assistant, always ready to help 🚀" }} }}

# User: "What day is it?"  
# → Response: {{ "intent": "chat", "arguments": {{ "message": "Today is {today_str}." }} }}

# User: "What is quantum computing?"  
# → Response: {{ "intent": "chat", "arguments": {{ "message": "search: What is quantum computing?" }} }}

# User: "Latest news in Hyderabad"  
# → Response: {{ "intent": "chat", "arguments": {{ "message": "search: Latest news in Hyderabad" }} }}

# User: "Who is the CEO of Tesla?"  
# → Response: {{ "intent": "chat", "arguments": {{ "message": "search: CEO of Tesla" }} }}

# ---

# 💬 Examples for other intents (DO NOT use chat intent):

# User: "Schedule team sync on April 5 at 3 PM"  
# → Response: {{ "intent": "create_event", "arguments": {{ "title": "team sync", "date": "2024-04-05", "time": "15:00" }} }}

# User: "What courses am I taking?"  
# → Response: {{ "intent": "get_current_courses", "arguments": {{ }} }}

# User: "Show all my events"  
# → Response: {{ "intent": "get_all_events", "arguments": {{ }} }}

# 13. get_unread_emails  
# → args: { {}}  
# Use this when the user says: "Check my emails", "Do I have unread emails?", "Show latest emails", etc.
# ✅ Always reply with ONLY valid JSON (no markdown or extra text).

# """


#     data = {
#         "model": "deepseek/deepseek-v3-base:free",
#         "messages": [
#             {
#                 "role": "system",
#                 "content": function_guide
#             },
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ]
#     }

#     try:
#         response = requests.post(OPENROUTER_URL, headers=headers, json=data)
#         json_response = response.json()
#         print("LLM Full Response:", json_response)

#         return json_response["choices"][0]["message"]["content"]
#     except Exception as e:
#         print("LLM Error:", e)
#         return json.dumps({
#             "intent": "chat",
#             "arguments": {"message": "Something went wrong trying to understand your command."}
#         })


# --------------------- Intent Routing ---------------------
def route_intent(intent, args):
    # print("Routing intent:", intent, "with args:", args)
    if intent == "get_time":
        return f"🕒 The current time is {datetime.now().strftime('%I:%M %p')}"

    elif intent == "create_event":
        title, date, time = args.get("title"), args.get("date"), args.get("time")
        if not all([title, date, time]):
            return "❌ Please provide title, date (YYYY-MM-DD), and time (HH:MM)."
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        return calendar_service.create_event(title, dt)
    elif intent == "get_unread_emails":
        emails = gmail_service.get_unread_emails()
        return "\n\n".join(emails)

    elif intent == "get_event":
        events = calendar_service.get_events(5)
        return format_events(events)

    elif intent == "get_all_events":
        events = calendar_service.get_all_events()
        return format_events(events)

    elif intent == "get_event_by_range":
        start_date = args.get("start_date")
        end_date = args.get("end_date")
        if not (start_date and end_date):
            return "❌ Provide both 'start_date' and 'end_date'."
        events = calendar_service.get_event_by_range(start_date, end_date)
        return format_events(events)

    elif intent == "get_current_courses":
        courses = get_current_courses()
        return "📘 Current Courses:\n" + "\n".join(f"- {c.name}" for c in courses)

    elif intent == "get_course_list":
        return get_course_list()

    elif intent == "get_upcoming_assignments":
        return format_assignments(get_upcoming_assignments())

    elif intent == "get_grades":
        return get_grades()

    elif intent == "sync_assignments_to_google_calendar":
        return sync_assignments_to_google_calendar()
    elif intent == "chat":
        message = args.get("message", "Hi there 👋")
        print("Chat intent detected with message:", message)

        # 🛑 NEW: Only trigger search if message starts with 'search:'
        if message.lower().startswith("search:"):
            search_query = message[7:].strip()
            if search_query:
                try:
                    search_results = web_search(search_query)
                    if search_results:
                        return f"🔍 {search_results}"
                except Exception as e:
                    print(f"Search failed: {e}")
                    return "⚠️ I tried to search but ran into a problem."

        return message


    elif intent == "get_event_by_date":
        print("Fetching events for date:", args)
        date = args.get("date")
        if not date:
            return "❌ Please provide the 'date' in YYYY-MM-DD format."
        events = calendar_service.get_event_by_date(date)
        return format_events(events)

    return "🤖 Sorry, I don't know how to handle that."

def format_events(events):
    if not events:
        return "📜 No events found."
    return "\n".join([
        f"📅 {e.get('summary', 'No Title')} at {e['start'].get('dateTime', e['start'].get('date'))}"
        for e in events
    ])

# --------------------- Flask Routes ---------------------
@app.route('/api/emails/important', methods=['GET'])
def get_important_emails():
    emails = gmail_service.get_unread_emails(max_results=5)
    return jsonify({"important": emails})



@app.route('/process', methods=['POST', 'OPTIONS'])
def process_command():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    data = request.get_json()
    user_input = data.get("input", "")
    print("User said:", user_input)

    intent_payload_raw = call_llm(user_input)

    try:
        if isinstance(intent_payload_raw, str):
            # Clean up if LLM wrapped it with ```json ... ```
            intent_payload_clean = intent_payload_raw.strip()
            if intent_payload_clean.startswith("```json"):
                intent_payload_clean = intent_payload_clean[7:].strip("`").strip()
            elif intent_payload_clean.startswith("```"):
                intent_payload_clean = intent_payload_clean[3:].strip("`").strip()

            intent_payload = json.loads(intent_payload_clean)
        else:
            intent_payload = intent_payload_raw
    except Exception as e:
        print("❌ Failed to parse intent payload:", e)
        return _corsify_actual_response(jsonify({
            "status": "error",
            "response": "⚠️ Invalid response from language model."
        }))

    intent = intent_payload.get("intent")
    args = intent_payload.get("arguments", {})

    if intent not in SUPPORTED_INTENTS:
        return jsonify({"status": "error", "response": f"❌ Unsupported intent: {intent}"})

    response = route_intent(intent, args)
    return _corsify_actual_response(jsonify({"status": "success", "response": response}))

@app.route('/api/calendar/events', methods=['GET'])
def get_calendar_events():
    print("Fetching all calendar events...")
    try:
        events = calendar_service.get_all_events()
        # print("✅ Fetched events:", events)
        return jsonify(events)
    except Exception as e:
        import traceback
        print("❌ Error in /api/calendar/events:")
        # traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --------------------- CORS Helpers ---------------------
def _build_cors_preflight_response():
    response = jsonify({'status': 'preflight'})
    response.headers.add("Access-Control-Allow-Origin", "http://localhost:5176")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "http://localhost:5176")
    return response


def is_factual_question(text):
    """Determine if a question would benefit from web search"""
    question_words = ["who", "what", "when", "where", "why", "how", "which", "is", "are", "can", "does"]
    text_lower = text.lower()
    return (text_lower.endswith('?') or 
            any(text_lower.startswith(word) for word in question_words) or
            "current" in text_lower or 
            "latest" in text_lower)

def extract_search_query(text):
    """Clean up the query for better search results"""
    # Remove question marks and common prefixes
    clean_text = re.sub(r'^(who|what|when|where|why|how|is|are|can|does)\s', '', text.lower())
    clean_text = clean_text.replace('?', '').strip()
    return clean_text if clean_text else None

# --------------------- Run Server ---------------------
if __name__ == '__main__':
    # Start email checking in a background thread
    # email_thread = threading.Thread(target=start_periodic_check, kwargs={"interval_minutes": 1}, daemon=True)
    # email_thread.start()

    # Start Flask server
    app.run(debug=True, port=5000)

