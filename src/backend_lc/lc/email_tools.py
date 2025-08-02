from langchain.tools import Tool
from pydantic import BaseModel, Field
from lc.config import get_llm
from textwrap import shorten

llm = get_llm()

# ──────────────────────────────
# Pydantic schema for arguments
# ──────────────────────────────
class ReplyToolInput(BaseModel):
    subject: str = Field(..., description="Email subject")
    snippet: str = Field(..., description="Email snippet or body")
    perspective: str = Field(..., description="Goal/tone, e.g. 'be polite'")
    user_name: str | None = Field(None, description="Display name of the sender (optional)")

# ──────────────────────────────
# Synchronous tool for the agent
# ──────────────────────────────

def _draft_reply_sync(subject: str,
                      snippet: str,
                      perspective: str,
                      user_name: str | None = None) -> str:
    """Return a drafted email body (plain‑text) from the user's perspective.

    This implementation is synchronous so it can be called directly by
    LangChain's StructuredChatAgent without hitting asyncio.run() issues.
    """
    # Truncate long snippets to keep prompt within model context limits.
    snippet = shorten(snippet or "", width=1500, placeholder="…")
    sender = user_name or "I"  # fallback pronoun if not provided

    prompt = (
        f"You are {sender}. Draft an email reply that {perspective}.\n"
        f"SUBJECT: {subject}\n"
        f"EMAIL SNIPPET:\n{snippet}\n\n"
        "Return only the email body, no subject line."
    )

    response = llm.invoke(prompt)
    return response.content.strip()



draft_reply_tool = Tool(
    name="draft_reply_tool",
    description=(
        "Draft an email reply. Required args: subject, snippet, "
        "perspective. Optional arg: user_name for first‑person tone."
    ),
    args_schema=ReplyToolInput,
    func=_draft_reply_sync,
)
