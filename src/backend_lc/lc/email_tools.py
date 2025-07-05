from langchain.tools import tool
from pydantic import BaseModel, Field
from lc.config import get_llm
from datetime import datetime

# Get the base LLM instance
llm = get_llm()

class ReplyToolInput(BaseModel):
    """Input model for the draft_reply_tool."""
    subject: str = Field(description="The subject of the email to reply to.")
    snippet: str = Field(description="The short snippet or body of the email content.")
    perspective: str = Field(description="The user's specific goal or tone for the reply, e.g., 'be polite', 'decline the offer'.")

@tool("draft_reply_tool", args_schema=ReplyToolInput)
def draft_reply_tool(subject: str, snippet: str, perspective: str) -> str:
    """
    Drafts a helpful and context-aware email reply from the user's perspective.
    This tool should be used to generate the final text for an email draft.
    """
    print("--- Running draft_reply_tool ---")

    # The detailed prompt engineering now lives inside the tool.
    prompt = f"""
    You are Druv, an AI assistant helping a user named Kalyan Raju draft an email reply.

    **Your Mission:**
    Your mission is to draft a reply from Kalyan's perspective with the following specific goal or tone: '{perspective}'

    ⚠️ **CRITICAL POINT OF VIEW INSTRUCTION:**
    You MUST write the draft as if you ARE Kalyan. Use personal pronouns like "I", "my", and "me".
    DO NOT refer to Kalyan as 'he' or 'you'.

    **Provided Email Context:**
    -   Subject: "{subject}"
    -   Snippet: "{snippet}"

    Generate only the body of the email reply. Do not add a subject line.
    """

    # The tool calls the base LLM directly, not the agent, to avoid a loop.
    ai_response = llm.invoke(prompt)

    # The `content` attribute holds the string response from the LLM
    return ai_response.content