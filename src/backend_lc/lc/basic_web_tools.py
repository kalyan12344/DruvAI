# In lc/basic_web_tools.py

import webbrowser
import platform  # To check the operating system
import subprocess # To run command-line operations
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class OpenUrlArgs(BaseModel):
    url: str = Field(..., description="The complete URL to open in the web browser, including http:// or https:// (e.g., https://www.google.com).")

@tool(args_schema=OpenUrlArgs)
def open_url_in_browser(url: str) -> str:
    """
    Opens the specified URL in a new tab.
    On macOS, it attempts to use Google Chrome specifically. On other systems, or if Chrome is not found on macOS,
    it uses the user's default web browser.
    This is primarily for displaying a webpage to the user.
    The agent cannot directly read or interact with the content of the opened tab.
    The URL must be complete and start with 'http://' or 'https://'.
    """
    if not isinstance(url, str):
        return "Error: URL must be a string."
    if not (url.startswith("http://") or url.startswith("https://")):
        return "Error: Invalid URL. The URL must start with 'http://' or 'https://'."

    try:
        system_os = platform.system()
        if system_os == "Darwin":  # Darwin is the system name for macOS
            try:
                # Attempt to open specifically in Google Chrome on macOS
                # Using 'open -a <Application Name> <url>'
                subprocess.run(["open", "-a", "Google Chrome", url], check=True)
                return f"Successfully requested to open {url} in Google Chrome."
            except FileNotFoundError: # 'open' command not found (highly unlikely on macOS) or Chrome not found
                opened_in_default = webbrowser.open_new_tab(url)
                if opened_in_default:
                    return f"Google Chrome application not found. Opened {url} in your default browser instead."
                else:
                    return f"Google Chrome application not found. Attempted to open in default browser, but it might not have responded."
            except subprocess.CalledProcessError as e_chrome: # 'open -a Google Chrome' failed for some reason
                opened_in_default = webbrowser.open_new_tab(url)
                if opened_in_default:
                    return f"Error trying to open specifically in Google Chrome (Error: {e_chrome}). Opened {url} in your default browser instead."
                else:
                    return f"Error trying to open specifically in Google Chrome (Error: {e_chrome}). Attempted default browser, but it might not have responded."
        else:
            # For other OS (Windows, Linux), use the default webbrowser behavior
            opened = webbrowser.open_new_tab(url)
            if opened:
                return f"Successfully requested to open {url} in your default web browser."
            else:
                return f"Attempted to open {url}, but your default browser might not have responded."
    except Exception as e:
        return f"An unexpected error occurred while trying to open the URL {url}: {str(e)}"