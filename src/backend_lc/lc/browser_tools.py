# lc/browser_tools.py

import time
from playwright.sync_api import sync_playwright, Page, Error as PlaywrightError, TimeoutError
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# --- [Keep your existing code for state management here] ---
_PLAYWRIGHT_INSTANCE = None
_PLAYWRIGHT_BROWSER = None
_PLAYWRIGHT_CONTEXT = None
_PLAYWRIGHT_PAGE: Page | None = None

def _ensure_browser_is_running(headless=False) -> Page:
    """Ensures Playwright browser is running and returns an active page."""
    global _PLAYWRIGHT_INSTANCE, _PLAYWRIGHT_BROWSER, _PLAYWRIGHT_CONTEXT, _PLAYWRIGHT_PAGE

    if _PLAYWRIGHT_PAGE and not _PLAYWRIGHT_PAGE.is_closed():
        return _PLAYWRIGHT_PAGE

    if _PLAYWRIGHT_BROWSER and _PLAYWRIGHT_BROWSER.is_connected():
        try: _PLAYWRIGHT_BROWSER.close()
        except Exception: pass
    if _PLAYWRIGHT_INSTANCE:
        try: _PLAYWRIGHT_INSTANCE.stop()
        except Exception: pass

    _PLAYWRIGHT_INSTANCE = sync_playwright().start()
    try:
        _PLAYWRIGHT_BROWSER = _PLAYWRIGHT_INSTANCE.chromium.launch(headless=headless)
        _PLAYWRIGHT_CONTEXT = _PLAYWRIGHT_BROWSER.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        )
        _PLAYWRIGHT_PAGE = _PLAYWRIGHT_CONTEXT.new_page()
        print("Playwright browser session started/restarted (visible).")
        return _PLAYWRIGHT_PAGE
    except Exception as e:
        print(f"Critical error initializing Playwright: {e}")
        if _PLAYWRIGHT_INSTANCE:
            try: _PLAYWRIGHT_INSTANCE.stop()
            except Exception: pass
        _PLAYWRIGHT_INSTANCE = None
        raise PlaywrightError(f"Failed to initialize browser: {e}")
def _scroll_page_to_bottom(page: Page):
    """Internal helper function to scroll a page to the bottom."""
    try:
        print("Scrolling page to bottom to ensure all content is loaded...")
        last_height = page.evaluate("() => document.body.scrollHeight")
        for i in range(10): # Limit scrolls
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2500) # Wait for content to load
            new_height = page.evaluate("() => document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        print("Finished scrolling.")
    except Exception as e:
        print(f"An error occurred while scrolling: {e}")
# --- Tool Definitions ---

class NavigateURLArgs(BaseModel):
    url: str = Field(..., description="The full URL to navigate to (e.g., https://www.google.com).")

@tool(args_schema=NavigateURLArgs)
def navigate_to_page(url: str) -> str:
    """
    Navigates to a URL, handles cookie banners, and scrolls down on Google pages.
    This should be the first browser action.
    Returns the page title or an error.
    """
    if not (url.startswith("http://") or url.startswith("https://")):
        return "Error: Invalid URL. Must start with http:// or https://."
    try:
        page = _ensure_browser_is_running(headless=False)
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # --- NEW: ATTEMPT TO DISMISS COOKIE/CONSENT BANNERS ---
        # This is crucial for interacting with the page.
        print("Attempting to dismiss cookie/consent banners...")
        consent_selectors = [
            "button:has-text('Accept all')",
            "button:has-text('Accept')",
            "button:has-text('Agree')",
            "button:has-text('Consent')",
            "button:has-text('I agree')",
        ]
        banner_clicked = False
        for selector in consent_selectors:
            try:
                button = page.query_selector(selector)
                if button and button.is_visible():
                    button.click(timeout=2000)
                    print(f"Clicked consent button with selector: '{selector}'")
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                    banner_clicked = True
                    break # Exit after successfully clicking one
            except (PlaywrightError, TimeoutError):
                # Ignore errors if a selector doesn't exist or times out
                continue
        if not banner_clicked:
            print("No common consent banners found or clicked.")


        # --- IMPROVED SCROLLING LOGIC ---
        scroll_message = ""
        # Using ".google." is more robust for international domains (e.g., google.co.uk)
        if ".google." in page.url:
            print("Google page detected. Starting scroll to bottom...")
            last_height = page.evaluate("() => document.body.scrollHeight")
            
            for i in range(10): # Limit scrolls to prevent infinite loops
                # Scroll down using JavaScript
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                # Wait for a longer, fixed period to allow content to load.
                page.wait_for_timeout(2500)

                new_height = page.evaluate("() => document.body.scrollHeight")
                print(f"Scroll attempt {i+1}: Old height={last_height}, New height={new_height}")

                if new_height == last_height:
                    print("Scroll height did not change. Reached bottom.")
                    break
                last_height = new_height
            
            scroll_message = " Scrolled to the bottom of the page to load all results."
            print("Finished scrolling.")

        title = page.title()
        return f"Successfully navigated to {url}. Page title: '{title}'.{scroll_message}"
    except TimeoutError as e_timeout:
        return f"Playwright timeout error navigating to {url}: {str(e_timeout).splitlines()[0]}"
    except PlaywrightError as e_playwright:
        return f"Playwright error navigating to {url}: {str(e_playwright).splitlines()[0]}"
    except Exception as e_general:
        return f"An unexpected error occurred during navigation to {url}: {str(e_general)}"

# --- [Keep your other tools (type_text, click_element, etc.) here] ---
class TypeTextArgs(BaseModel):
    selector: str = Field(..., description="CSS selector for the input field (e.g., 'input[name=\"q\"]', '#searchBarId').")
    text_to_type: str = Field(..., description="The text to type into the input field.")
    press_enter_after: bool = Field(default=False, description="Whether to simulate pressing Enter key after typing.")
    delay_per_character_ms: int = Field(default=50, description="Delay in milliseconds between keystrokes for more human-like typing. Set to 0 for instant fill.")

@tool(args_schema=TypeTextArgs)
def type_text_in_element(selector: str, text_to_type: str, press_enter_after: bool = False, delay_per_character_ms: int = 50) -> str:
    """
    Finds an element on the current page using its CSS selector and types the given text into it.
    
    Optionally presses Enter after typing. Use after 'navigate_to_page'.
    """
    if _PLAYWRIGHT_PAGE is None or _PLAYWRIGHT_PAGE.is_closed():
        return "Error: No active browser page. Use 'navigate_to_page' first."
    try:
        element = _PLAYWRIGHT_PAGE.query_selector(selector)
        if not element:
            return f"Error: Could not find element with selector '{selector}'."
        
        if delay_per_character_ms > 0:
            element.type(text_to_type, delay=delay_per_character_ms)
        else:
            element.fill(text_to_type) # Faster, less "human-like"
        
        action_taken = f"Typed '{text_to_type}' into element '{selector}'."
        
        if press_enter_after:
            element.press("Enter")
            action_taken += " Pressed Enter."
            _PLAYWRIGHT_PAGE.wait_for_load_state("domcontentloaded", timeout=20000) # Wait for potential navigation
        
        return action_taken
    except TimeoutError as e_timeout:
        return f"Playwright timeout error while typing or pressing Enter in '{selector}': {str(e_timeout).splitlines()[0]}"
    except PlaywrightError as e_playwright:
        return f"Playwright error while interacting with '{selector}': {str(e_playwright).splitlines()[0]}"
    except Exception as e_general:
        return f"An unexpected error occurred while interacting with '{selector}': {str(e_general)}"

class ClickElementArgs(BaseModel):
    selector: str = Field(..., description="CSS selector for the element to click (e.g., 'button[type=\"submit\"]', '#loginButton').")

@tool(args_schema=ClickElementArgs)
def click_element_on_page(selector: str) -> str:
    """
    Finds an element on the current page using its CSS selector and clicks it.
        if the task is to post in linked in then search for selector="button span:has-text('Start a post')"

    Use after 'navigate_to_page' and other interactions.
    """
    if _PLAYWRIGHT_PAGE is None or _PLAYWRIGHT_PAGE.is_closed():
        return "Error: No active browser page. Use 'navigate_to_page' first."
    try:
        element = _PLAYWRIGHT_PAGE.query_selector(selector)
        if not element:
            return f"Error: Could not find element with selector '{selector}' to click."
        
        element.click()
        # Consider adding a wait_for_load_state or wait_for_navigation if clicks cause page changes
        _PLAYWRIGHT_PAGE.wait_for_load_state("domcontentloaded", timeout=20000) # Example wait
        return f"Successfully clicked element with selector '{selector}'."
    except TimeoutError as e_timeout:
        return f"Playwright timeout error while clicking '{selector}': {str(e_timeout).splitlines()[0]}"
    except PlaywrightError as e_playwright:
        return f"Playwright error while clicking '{selector}': {str(e_playwright).splitlines()[0]}"
    except Exception as e_general:
        return f"An unexpected error occurred while clicking '{selector}': {str(e_general)}"

@tool
def get_visible_text_from_page() -> str:
    """
    Fetches all visible text content from the current browser page.
    Use this after navigation or interactions to understand the page content.
    Returns a summary of the text or an error message.
    """
    if _PLAYWRIGHT_PAGE is None or _PLAYWRIGHT_PAGE.is_closed():
        return "Error: No active browser page. Use 'navigate_to_page' first."
    try:
        # Using evaluate to get innerText is often better than full HTML for LLMs
        _scroll_page_to_bottom(_PLAYWRIGHT_PAGE)

        all_text = _PLAYWRIGHT_PAGE.evaluate("() => document.body.innerText")
        if all_text:
            # Return a manageable portion, e.g., first 2000 characters
            return f"Visible text content from current page (first 2000 chars):\n{all_text[:2000].strip()}"
        else:
            return "No visible text content found on the page or page is empty."
    except PlaywrightError as e_playwright:
        return f"Playwright error while getting page text: {str(e_playwright).splitlines()[0]}"
    except Exception as e_general:
        return f"An unexpected error occurred while getting page text: {str(e_general)}"

@tool
def close_browser_session() -> str:
    """
    Closes the currently active browser session controlled by Playwright.
    Use this when a web interaction task is fully complete or if errors occur.
    """
    global _PLAYWRIGHT_PAGE, _PLAYWRIGHT_CONTEXT, _PLAYWRIGHT_BROWSER, _PLAYWRIGHT_INSTANCE
    try:
        if _PLAYWRIGHT_BROWSER and _PLAYWRIGHT_BROWSER.is_connected():
            _PLAYWRIGHT_BROWSER.close()
        if _PLAYWRIGHT_INSTANCE:
            _PLAYWRIGHT_INSTANCE.stop()
        message = "Playwright browser session closed."
    except Exception as e:
        message = f"Error closing browser session: {e}"
    finally: # Ensure globals are reset
        _PLAYWRIGHT_PAGE = None
        _PLAYWRIGHT_CONTEXT = None
        _PLAYWRIGHT_BROWSER = None
        _PLAYWRIGHT_INSTANCE = None
        print(message)
    return message