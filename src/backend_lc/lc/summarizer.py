from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from lc.config import get_llm

llm = get_llm()

# --- summarize_page Tool (with Structured Prompt) ---
class SummArgs(BaseModel):
    page_content: str = Field(..., description="Raw visible text of a webpage")

@tool(args_schema=SummArgs)
def summarize_page(page_content: str) -> str:
    """Summarizes webpage content into a structured Markdown format."""
    print("📝 Generating structured page summary...")
    
    summarization_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert analyst. Your task is to read the provided text from a webpage and create a concise, structured summary.

**CRITICAL FORMATTING RULES:**
1.  The entire output **MUST** be in Markdown format.
2.  Start with a `## Summary` heading.
3.  Below the heading, provide a 2-3 sentence overview of the main topic.
4.  After the overview, create a `### Key Takeaways` subheading.
5.  Under "Key Takeaways", list the 3-5 most important points as a bulleted list.
6.  Bold any key terms, names, or data points."""),
        ("user", """
**WEBPAGE CONTENT:**
---
{page_content}
---

Now, generate the structured Markdown summary.""")
    ])
    
    chain = summarization_prompt | llm
    response = chain.invoke({"page_content": page_content})
    
    print("✅ Page summary complete.")
    return response.content

# --- analyze_page Tool (with Structured Prompt) ---
class AnalyzeArgs(BaseModel):
    page_content: str
    question: str

@tool(args_schema=AnalyzeArgs)
def analyze_page(page_content: str, question: str) -> str:
    """Answers a specific question using only the provided page_content and returns a structured answer."""
    print(f"📝 Answering question: '{question}'...")

    analysis_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a meticulous research assistant. Your goal is to answer a user's question based *strictly* on the provided text content.

**CRITICAL INSTRUCTIONS:**
1.  Answer the question directly and concisely.
2.  Format your answer using Markdown.
3.  If the answer involves a list of items, use a bulleted list.
4.  If you are quoting directly from the text, use Markdown blockquotes (`>`).
5.  If the text does not contain the answer, you **MUST** state: "The provided text does not contain an answer to this question." """),
        ("user", """
**PROVIDED TEXT:**
---
{page_content}
---

**QUESTION:**
{question}

Now, provide the structured answer.""")
    ])

    chain = analysis_prompt | llm
    response = chain.invoke({"page_content": page_content, "question": question})

    print("✅ Page analysis complete.")
    return response.content