from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain.schema import Document
from langchain.chains.summarize import load_summarize_chain
from lc.config import get_llm

# ─────────── summarize_page ───────────────────────────────────
class SummArgs(BaseModel):
    page_content: str = Field(..., description="Raw visible text of a webpage")

@tool(args_schema=SummArgs)
def summarize_page(page_content: str) -> str:
    """Summarise webpage content in ≤ 200 words (no mention of Druv)."""
    docs = [Document(page_content=page_content)]
    return load_summarize_chain(get_llm(), chain_type="stuff").run(docs)

# ─────────── analyze_page ─────────────────────────────────────
class AnalyzeArgs(BaseModel):
    page_content: str
    question: str

@tool(args_schema=AnalyzeArgs)
def analyze_page(page_content: str, question: str) -> str:
    """Answer *question* using ONLY *page_content*."""
    prompt = f"Page:\n{page_content}\n\nQuestion: {question}"
    return get_llm().invoke(prompt).content
