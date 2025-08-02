#lc/email_tools.py

from langchain.tools import tool
from pydantic import BaseModel, Field
from lc.config import get_llm
from datetime import datetime

llm = get_llm()

class ReplyToolInput(BaseModel):
    subject: str = Field(description="The subject of the email to reply to.")
    snippet: str = Field(description="The short snippet or body of the email content.")
    perspective: str = Field(description="The user's specific goal or tone for the reply, e.g., 'be polite', 'decline the offer'.")
    user_name: str = Field(description="The name of the user sending the email.") # Added for context

@tool("draft_reply_tool", args_schema=ReplyToolInput)
async def draft_reply_tool(subject: str, snippet: str, perspective: str, user_name: str) -> str:
    """Drafts a helpful and context-aware email reply from the user's perspective."""
    # FIX: Prompt is now dynamic and no longer hardcoded.
    prompt = f"""
    You are an AI assistant helping a user named {user_name} draft an email reply.
    Your mission is to write a reply from {user_name}'s perspective with the following goal: '{perspective}'
    You MUST write the draft as if you ARE {user_name}. Use personal pronouns like "I", "my", and "me".
    
    EMAIL CONTEXT:
    - Subject: "{subject}"
    - Snippet: "{snippet}"

    Generate only the body of the email reply. Do not add a subject line.
    """
    # FIX: Uses the async 'ainvoke' method for better performance.
    ai_response = await llm.ainvoke(prompt)
    return ai_response.content