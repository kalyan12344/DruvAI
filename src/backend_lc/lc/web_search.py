import os
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.tools import tool

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX_ID = os.getenv("CX_ID")

def _scrape_article_text(url: str) -> str | None:
    """Scrapes the primary text content from a given URL."""
    try:
        print(f"🔍 Scraping: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 100])

        if text and len(text) > 400:
            print(f"✅ Extracted {len(text)} characters using BeautifulSoup.")
            return text[:8000]

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

class WebResearchArgs(BaseModel):
    query: str = Field(..., description="The specific question or topic to research on the web.")

@tool(args_schema=WebResearchArgs)
def web_search(query: str) -> str:
    """
    Gathers raw information about a topic from the web by scraping top search results.
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
                "num": 5  # Fetches top 5 results
            }
        )
        response.raise_for_status()
        search_data = response.json()
        items = search_data.get("items", [])
        
        if not items:
            return "No search results found."
            
    except Exception as e:
        return f"Failed to fetch search results from Google API: {e}"

    collected_content = []
    for item in items:
        url = item.get("link")
        if url:
            scraped_text = _scrape_article_text(url)
            if scraped_text:
                collected_content.append(scraped_text)

    if not collected_content:
        return "Could not extract any useful information from the top search results."

    return "\n\n---\n\n".join(collected_content)