# lc/research_tool.py

import os
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# --- Setup ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX_ID = os.getenv("CX_ID")


# --- Helper Function for Scraping ---

def _scrape_article_text(url: str) -> str | None:
    """Scrapes the primary text content from a given URL using requests and BeautifulSoup."""
    try:
        print(f"🔍 Scraping: {url}")
        headers = {
            # Using a standard browser User-Agent
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Primary method: BeautifulSoup to find long paragraphs
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 100])

        if text and len(text) > 400:
            print(f"✅ Extracted {len(text)} characters using BeautifulSoup.")
            return text[:8000]

        # Fallback method: newspaper3k
        print("ℹ️ Falling back to newspaper3k for content extraction...")
        article = Article(url)
        article.download()
        article.parse()
        
        if article.text:
             print(f"✅ Extracted {len(article.text)} characters using newspaper3k.")
             return article.text[:8000]

        return None

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return None


# --- Main Tool Definition ---

class WebResearchArgs(BaseModel):
    query: str = Field(..., description="The specific question or topic to research on the web.")

@tool(args_schema=WebResearchArgs)
def web_search(query: str) -> str:
    """
    Gathers raw information about a topic from the web using the Google Custom Search API.

    This tool performs these steps:
    1. Searches Google for a query.
    2. Scrapes the content from the top 5 results.
    3. Returns the combined, unprocessed text from all sources.
    This output is ideal for feeding into a separate tool for summarization.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CX_ID:
        return "Error: GOOGLE_API_KEY or GOOGLE_CX_ID environment variables are not set."

    print(f"🔎 Starting web research for query: '{query}' using Google Custom Search.")
    
    try:
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CX_ID,
                "q": query,
                "num": 2  # Fetch top 5 results
            }
        )
        response.raise_for_status()
        search_data = response.json()
        items = search_data.get("items", [])
        
        if not items:
            return "No search results found."
            
    except Exception as e:
        return f"Failed to fetch search results from Google API: {e}"

    # Scrape content from each result
    collected_content = []
    for item in items:
        url = item.get("link")
        title = item.get("title", "Untitled")
        snippet = item.get("snippet", "")
        if url:
            scraped_text = _scrape_article_text(url)
            if scraped_text:
                collected_content.append(
                    f"Source Title: {title}\n"
                    f"URL: {url}\n"
                    f"Initial Snippet: {snippet}\n\n"
                    f"Scraped Content:\n{scraped_text}\n"
                    "---"
                )

    if not collected_content:
        return "Could not extract any useful information from the top search results."

    # Return the combined raw text from all sources
    return "\n\n".join(collected_content)