# Re-export all tools for easy import
from .calendar import (
    find_dates,
    get_events_on_date,
    get_events_in_range,
    create_event,
    delete_event,
    get_current_date,
    _parse_date_fallback
)

from .browser_tools import (
    navigate_to_page, 
    type_text_in_element, 
    click_element_on_page,
    get_visible_text_from_page,
    close_browser_session 
)

from .summarizer import summarize_page, analyze_page
from .browser_automation_tools import navigate_and_get_title
from .basic_web_tools import open_url_in_browser

from .places_tool import query_place_information
from .web_search import web_search

# --- NEW: Import the structured formatting tools ---
from .structured_tools import (
    format_confirmation,
    format_calendar_view,
    format_news_summary
)
from .task_tools import create_task_tool, delete_task_tool
from .email_tools import draft_reply_tool
from .shipping_tools import  nike_order_lookup
from .reminder_tools import create_reminder_tool, delete_reminder_tool,check_reminder_exists, list_all_reminders
from .retrieval_tools import search_user_documents 


ALL_TOOLS = [
    # Calendar Tools
    find_dates,
    get_current_date,
    get_events_on_date,
    get_events_in_range,
    create_event,
    delete_event,
    draft_reply_tool,
    create_task_tool,
    delete_task_tool,
    create_reminder_tool,
    delete_reminder_tool,
    check_reminder_exists,
    list_all_reminders,
    # Page Analysis Tools
    summarize_page,
    analyze_page,
    
    # Browser Automation Tools
    navigate_to_page,
    type_text_in_element,
    click_element_on_page,
    get_visible_text_from_page,
    close_browser_session,
    
    # General Web Tools
    query_place_information,
    web_search,
    
    # --- NEW: Add the formatting tools to the list ---
    format_confirmation,
    format_calendar_view,
    format_news_summary,

    # Shipping Tools
    # track_standard_carrier,
    nike_order_lookup,

    #doc tools
    search_user_documents

]