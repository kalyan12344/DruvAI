import json
import ast
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from lc.config import get_llm

llm = get_llm()

# --- Pydantic Models for Type Safety ---
class Event(BaseModel):
    summary: str
    start_time: Optional[str]
    end_time: Optional[str]
    htmlLink: Optional[str] = None

class CalendarView(BaseModel):
    response_type: Literal["calendar_view"]
    message: str
    events: List[Event]

class NoEventsFound(BaseModel):
    response_type: Literal["no_events"]
    message: str

class SimpleConfirmation(BaseModel):
    response_type: Literal["confirmation"]
    status: Literal["success", "error"]
    message: str

# --- Tool Argument Schemas ---
class FormatArgs(BaseModel):
    data: Any = Field(..., description="The raw data to be formatted, usually a string or dictionary from a previous tool.")

class RichSummaryArgs(BaseModel):
    raw_text: str = Field(..., description="The raw, unprocessed text gathered from a web search.")
    original_query: str = Field(..., description="The user's original question or query.")

# --- Tools ---
@tool(args_schema=RichSummaryArgs)
def format_rich_summary(raw_text: str, original_query: str) -> str:
    """
    Takes raw text from a web search and synthesizes it into a rich, insightful,
    and highly organized briefing note in Markdown format. Use this for general research queries.
    """
    print("📝 Formatting raw text into a rich summary...")
    formatting_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a world-class research analyst. Your job is to synthesize raw text into a rich, organized briefing note.

**FORMATTING RULES:**
1.  The entire output **MUST** be in Markdown format.
2.  Create a main title prefixed with an emoji (e.g., 🚀, 💡).
3.  Identify 2-3 key themes and create subheadings for each.
4.  Under each subheading, list important details as bullet points.
5.  **Bold** key terms to make the summary easy to scan.
6.  You must only use information from the provided raw text.
"""),
        ("user", """
**Original Query:** "{original_query}"
**Raw Text from Web Search:**
---
{raw_text}
---
Now, generate the rich, structured Markdown briefing note.""")
    ])
    chain = formatting_prompt | llm
    response = chain.invoke({"raw_text": raw_text, "original_query": original_query})
    print("✅ Rich summary formatting complete.")
    return response.content

@tool(args_schema=FormatArgs)
def format_calendar_view(data: Any) -> Dict:
    """
    Takes raw data from a calendar tool and formats it into the standard
    'calendar_view' or 'no_events' JSON response for the frontend. Use this for all calendar queries.
    """
    event_data = data
    if isinstance(data, str):
        try: event_data = ast.literal_eval(data)
        except (ValueError, SyntaxError): event_data = {"status": data, "events": []}
    
    if not event_data or not event_data.get("events"):
        message = event_data.get("status", "No events found.") if event_data else "No events found."
        return NoEventsFound(message=message).model_dump()
    
    status_message = event_data.get("status", "Here are your events.")
    events = event_data.get("events", [])
    simplified_events = []
    for event in events:
        start = event.get("start", {})
        end = event.get("end", {})
        simplified_events.append({
            "summary": event.get("summary", "No Title"),
            "start_time": start.get("dateTime", start.get("date")),
            "end_time": end.get("dateTime", end.get("date")),
            "htmlLink": event.get("htmlLink")
        })
    return CalendarView(response_type="calendar_view", message=status_message, events=simplified_events).model_dump()

@tool(args_schema=FormatArgs)
def format_confirmation(data: str) -> Dict:
    """
    Formats simple success or error messages into a standard confirmation JSON.
    """
    is_error = "error" in data.lower() or "fail" in data.lower() or "cannot" in data.lower()
    return SimpleConfirmation(
        status="error" if is_error else "success",
        message=data
    ).model_dump()