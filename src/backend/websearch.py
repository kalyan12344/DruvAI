import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from newspaper import Article
from openai import OpenAI

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX_ID = os.getenv("CX_ID")

# 🧠 Groq setup
groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def web_search(query, max_results=3):
    query = query.strip("search:").strip()
    if not GOOGLE_API_KEY or not GOOGLE_CX_ID:
        return "⚠️ Google API key or CX ID not set."
    print(f"🔎 Web search query: {query}")
    try:
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CX_ID,
                "q": query,
                "num": max_results
            }
        )

        data = response.json()
        items = data.get("items", [])

        if not items:
            return "😔 I couldn't find anything useful."

        collected = []
        for item in items:
            url = item["link"]
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            article = scrape_article_text(url)
            if article:
                collected.append(f"🔗 {title}\n{snippet}\n\n{article}")

        if not collected:
            return "😔 Couldn't extract enough information from sources."

        combined_text = "\n\n".join(collected)
        summary = summarize_text(combined_text, query)
        return f"📰 {summary.strip()}"

    except Exception as e:
        print("❌ Search error:", e)
        return "❌ Failed to fetch search results."


def scrape_article_text(url):
    try:
        print(f"🔍 Scraping: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; DruvBot/1.0)"
        }

        response = requests.get(url, headers=headers, timeout=5)
        print("🌐 Status code:", response.status_code)
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50])

        if text and len(text) > 300:
            print("✅ Extracted text using BeautifulSoup.")
            return text[:5000]

        print("ℹ️ Falling back to newspaper3k...")
        article = Article(url)
        article.download()
        article.parse()
        return article.text[:5000] if article.text else None

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return None


def summarize_text(text, query=""):
    try:
        prompt = (
            f"You are Druv, a helpful AI assistant. Based on the information below, answer the user's question as clearly, accurately, and briefly as possible.\n\n"
            f"User's question: \"{query}\"\n\n"
            f"Information:\n{text}\n\n"
            "Answer:"
        )

        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are an intelligent assistant that gives direct answers to user questions by analyzing provided content."},
                {"role": "user", "content": prompt}
            ]
        )

        summary = response.choices[0].message.content
        print("🧠 Summary:", summary)
        return summary

    except Exception as e:
        print("❌ Summarization/Answering error:", e)
        return "⚠️ I couldn't generate an answer, but you can check the sources directly."
