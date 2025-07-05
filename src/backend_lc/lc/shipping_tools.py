import re
from typing import Dict

from langchain.tools import tool
from pydantic import BaseModel, Field
from lc.config import get_llm
# --- Use the SYNCHRONOUS Playwright API ---
from playwright.sync_api import sync_playwright, Error as PlaywrightError

# --- Pydantic Models ---

class NikeOrderInput(BaseModel):
    """Input for looking up an order on Nike.com."""
    order_number: str = Field(description="The Nike order number.")
    user_email: str = Field(description="The user's email address used to place the order.")

# --- The Self-Contained Tool (Now Synchronous) ---

@tool("nike_order_lookup", args_schema=NikeOrderInput)
def nike_order_lookup(order_number: str, user_email: str) -> str:
    """
    Looks up a Nike order status by navigating directly to the order details URL,
    entering the email, clicking submit, scrolling the page, and reading the content.
    Use this for Nike orders.
    """
    print(f"--- TOOL: Running Self-Contained SYNC nike_order_lookup for order: {order_number} ---")
    
    with sync_playwright() as p:
        browser = None
        try:
            # Step 1: Launch a new browser instance for this task
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            print("--- Playwright sync session started for Nike lookup ---")

            # Step 2: Navigate directly to the order details page using the order number.
            order_url = f"https://www.nike.com/orders/details/{order_number}"
            page.goto(order_url, wait_until="domcontentloaded", timeout=30000)
            print(f"--- Navigated to Nike order page: {order_url} ---")

            # Step 3: Type the user's email into the correct input field.
            email_selector = "input[name='email']" 
            page.type(email_selector, user_email, delay=50)
            print(f"--- Typed user email ---")

            # Step 4: Click the submit/view order button.
            button_selector = "button[data-testid='lookup-submit']" 
            page.click(button_selector)
            print("--- Clicked submit button ---")

            # Wait for navigation after the click
            page.wait_for_load_state("domcontentloaded", timeout=20000)
            print("--- Order status page loaded ---")
            
            # --- UPDATED LOGIC: Scroll the entire page to load dynamic content ---
            print("--- Scrolling page to bottom ---")
            last_height = page.evaluate("() => document.body.scrollHeight")
            for _ in range(5): # Scroll a few times to be sure
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000) # Wait for content to load
                new_height = page.evaluate("() => document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            print("--- Finished scrolling ---")

            # Step 5: Get all visible text from the page.
            page_content = page.evaluate("() => document.body.innerText")
            print("--- Successfully retrieved page content ---")

            # Step 6: Use an LLM to summarize the page content for a clean response
            llm = get_llm()
            summarizer_prompt = f"Summarize the following text from a Nike order status page into a short, helpful status update. Extract the current status, estimated delivery date, and tracking number if available.\n\n{page_content[:2500]}"
            status_summary = llm.invoke(summarizer_prompt).content
            
            return status_summary

        except PlaywrightError as e:
            error_message = str(e).splitlines()[0]
            if "Timeout" in error_message:
                return f"The Nike website took too long to respond. This could be due to an incorrect order number/email or a temporary issue with their site."
            print(f"A Playwright error occurred: {error_message}")
            return f"An error occurred while trying to automate the Nike website: {error_message}."
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return f"An unexpected error occurred during the Nike order lookup process: {str(e)}"
        
        finally:
            # Step 7: Ensure the browser is always closed
            if browser:
                browser.close()
            print("--- Playwright sync session for Nike lookup closed ---")
