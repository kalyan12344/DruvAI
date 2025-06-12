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
ALL_TOOLS = [
    find_dates,
    get_current_date,
    get_events_on_date,
    get_events_in_range,
    create_event,
    delete_event,
    summarize_page,
    analyze_page,
    # open_url_in_browser,
    # navigate_and_get_title,
    # navigate_to_page,
    # type_text_and_submit_search,
    navigate_to_page,
    type_text_in_element,
    click_element_on_page,
    get_visible_text_from_page,
    close_browser_session,
    query_place_information,
    web_search
]
