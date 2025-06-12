# In lc/browser_automation_tools.py
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from playwright.sync_api import sync_playwright # For Playwright

class NavigateToURLArgs(BaseModel):
    url: str = Field(..., description="The full URL to navigate to (e.g., https://www.google.com).")

@tool(args_schema=NavigateToURLArgs)
def navigate_and_get_title(url: str) -> str:
    """
    Navigates to the given URL in a new browser page and returns the title of the page.
    The URL must start with http:// or https://.
    """
    if not (url.startswith("http://") or url.startswith("https://")):
        return "Error: Invalid URL. Must start with http:// or https://."
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=Falses) # Or headless=False to see it
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            title = page.title()
            browser.close()
            if title:
                return f"Navigated to {url}. Page title is: '{title}'"
            else:
                return f"Navigated to {url}, but the page has no title."
    except Exception as e:
        return f"Error during navigation to {url}: {str(e)}"