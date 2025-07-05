# lc/structured_tools.py
# A toolkit of formatters to generate specific, structured JSON outputs.

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from lc.config import get_llm
import json
import ast # Import the Abstract Syntax Tree library

# ==============================================================================
#  1. DEFINE ALL YOUR DESIRED JSON STRUCTURES (PYDANTIC MODELS)
# ==============================================================================

class SimpleConfirmation(BaseModel):
    """For simple success/failure messages, like creating or deleting an event."""
    response_type: Literal["confirmation"] = "confirmation"
    status: Literal["success", "error"]
    message: str = Field(description="A user-friendly message describing the result of the action.")

class Event(BaseModel):
    """A single calendar event."""
    summary: str
    start_time: Optional[str]
    end_time: Optional[str]

class CalendarView(BaseModel):
    """For displaying a user's schedule when events ARE found."""
    response_type: Literal["calendar_view"] = "calendar_view"
    message: str = Field(description="A concise summary, e.g., 'You have 3 events today.'")
    events: List[Event]

class NoEventsFound(BaseModel):
    """A specific response for when a user's calendar is empty."""
    response_type: Literal["no_events"] = "no_events"
    message: str = Field(description="A friendly message indicating there are no events.")

class NewsArticle(BaseModel):
    """A single news article."""
    headline: str
    source: str
    summary_points: List[str]

class NewsSummary(BaseModel):
    """For displaying a summary of news articles."""
    response_type: Literal["news_summary"] = "news_summary"
    message: str = Field(description="A high-level summary of the news topic.")
    articles: List[NewsArticle]


# ==============================================================================
#  2. CREATE A GENERIC HELPER FUNCTION TO RUN ANY FORMATTER
# ==============================================================================

def _get_structured_output(raw_data: str, pydantic_model: BaseModel):
    """A generic function to invoke the LLM with any Pydantic model."""
    parser = PydanticOutputParser(pydantic_object=pydantic_model)
    
    prompt = PromptTemplate(
        template="""
        You are a structured data formatting assistant for Druv AI. Your job is to take raw text or data and convert it into the required JSON format.
        
        Analyze the following data and respond ONLY with the correctly formatted JSON object.

        RAW DATA:
        {raw_data}
        
        {format_instructions}
        """,
        input_variables=["raw_data"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | get_llm() | parser
    response = chain.invoke({"raw_data": raw_data})
    return response.model_dump_json()


# ==============================================================================
#  3. CREATE THE SPECIALIZED LANGCHAIN TOOLS
# ==============================================================================

class FormatArgs(BaseModel):
    # We accept 'Any' to handle the incoming data flexibly.
    data: Any = Field(description="The raw data to be formatted, usually the output of a previous tool.")

@tool(args_schema=FormatArgs)
def format_confirmation(data: str) -> str:
    """
    Use this to format simple success or error messages after an action like creating,
    deleting, or updating something. The input should be a simple string like
    "Event created successfully" or "Error: Could not find event".
    """
    return _get_structured_output(data, SimpleConfirmation)


@tool(args_schema=FormatArgs, return_direct=True)
def format_calendar_view(data: Any) -> str:
    """
    Use this to format the user's daily schedule. It takes the raw output
    from the 'get_events_on_date' tool. If the list of events is empty, it should
    be formatted using the 'NoEventsFound' model. Otherwise, use the 'CalendarView' model.
    """
    event_data = None
    # --- THIS IS THE FIX ---
    # The agent passes a string representation of a dictionary.
    # We use `ast.literal_eval` to safely convert it into a real dictionary.
    if isinstance(data, str):
        try:
            event_data = ast.literal_eval(data)
        except (ValueError, SyntaxError):
            # If parsing fails, fall back to treating it as a plain string
            event_data = {"status": data, "events": []}
    elif isinstance(data, dict):
        event_data = data

    if not event_data or not event_data.get("events"):
        # Use the specific model for no events
        status_message = event_data.get("status", "No events found.") if event_data else "No events found."
        return _get_structured_output(status_message, NoEventsFound)
    else:
        # Use the model for displaying events.
        # Convert the dictionary back to a proper JSON string for the LLM.
        proper_json_string = json.dumps(event_data)
        return _get_structured_output(proper_json_string, CalendarView)


@tool(args_schema=FormatArgs)
def format_news_summary(data: str) -> str:
    """
    Use this to format a list of news articles into a structured summary.
    The input should be raw text containing news information.
    """
    return _get_structured_output(data, NewsSummary)
