from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.messages import HumanMessage # Keep if used elsewhere, not directly in run_agent
from langchain_core.tools import Tool # Keep if used elsewhere
from langchain import hub
from lc.config import get_llm
from lc import ALL_TOOLS
from datetime import datetime, timedelta
import re

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
 # Make sure this is correctly populated via lc/__init__.py
today = datetime.utcnow().strftime("%Y-%m-%d")

llm = get_llm()

SYSTEM_PROMPT = """
# MISSION
Your mission is to act as Druv, a proactive and intelligent voice-enabled AI personal assistant, to help the user efficiently and accurately accomplish their tasks.

# CRITICAL RESPONSE PROTOCOL - MUST FOLLOW EXACTLY
⚠️  **MANDATORY**: EVERY response must start with "Thought:" - NO EXCEPTIONS
⚠️  **MANDATORY**: You must use EXACTLY one of the two formats below - NEVER respond conversationally

---
**FORMAT 1: Using a Tool**
Thought: [Your reasoning, step-by-step plan, and justification for using a specific tool.]
Action:
```json
{{
  "action": "tool_name",
  "action_input": {{ "arg_name": "value" }}
}}
```

---
**FORMAT 2: Responding to the User (ONLY when you have complete information)**
Thought: [Your final reasoning before providing the answer. Summarize how you got the answer and why you are confident in it.]
Final Answer: [This is the response shown to the user. Be concise, friendly, and professional. Use clear Markdown formatting.]

# EXAMPLES OF CORRECT RESPONSES:

**Example 1 - When checking conflicts:**
Thought: The user wants to add an event but I need to check if they're free first. I found they have a shift from 6 PM to 9 PM today, so they're not free. I should tell the user they are not free.
Final Answer: I found you already have a shift scheduled from 6:00 PM to 9:00 PM today in ibaco. Since you're not free, I didn't add the new event.

**Example 2 - When using a tool:**
Thought: I need to check what events the user has today before I can determine if they're free.
Action:
```json
{{
  "action": "get_events_on_date",
  "action_input": {{ "date": "2025-06-08" }}
}}
```

# CORE DIRECTIVES
1. **Format Compliance**: NEVER respond without "Thought:" at the start
2. **Complete Information**: Only use "Final Answer:" when you have everything needed to fully respond
3. **Error Handling**: If tools fail, acknowledge in Thought and provide Final Answer explaining the issue
4. **Conditional Logic**: Always check conditions before acting (e.g., "if free" means check for existing events first)

# CONTEXT
Today's Date: {today}
Available tools: {tools}

⚠️  REMEMBER: Start EVERY response with "Thought:" and end with either Action or "Final Answer:"
"""

# SIMPLE ERROR HANDLER - This is the only addition you need
def fix_parsing_error(error):
    """Simple fix for parsing errors"""
    error_str = str(error)
    print(f"Caught parsing error: {error_str}")
    
    # Extract the actual response from the error
    if "Could not parse LLM output:" in error_str:
        # Find the response between "Could not parse LLM output:" and "For troubleshooting"
        start = error_str.find("Could not parse LLM output:") + len("Could not parse LLM output:")
        end = error_str.find("For troubleshooting")
        if end == -1:
            end = len(error_str)
        
        actual_response = error_str[start:end].strip()
        print(f"Extracted response: {actual_response}")
        
        # Return the response directly - LangChain will use this as the final answer
        return actual_response
    
    return "I encountered a formatting issue. Please try again."

# Use the hub prompt which handles agent_scratchpad correctly
prompt = hub.pull("hwchase17/structured-chat-agent")

# Customize the system message while keeping the proper structure
custom_prompt = prompt.partial(
    system_message=SYSTEM_PROMPT,
    today=today
)

agent = create_structured_chat_agent(
    llm=llm,
    tools=ALL_TOOLS,
    prompt=custom_prompt
)

# THE KEY CHANGE: Add the error handler here
SMART_AGENT = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=ALL_TOOLS,
    verbose=True,
    handle_parsing_errors=fix_parsing_error,  # <-- This is the fix
)

def run_agent(user_input: str | dict) -> str:
    final_agent_input_str = ""

    if isinstance(user_input, dict):
        question = user_input.get("question")
        page_content_from_input = user_input.get("page_content")

        if not question:
            return "Input dictionary is missing a 'question'. Please provide a question."
        
        final_agent_input_str = question # Start with the question

        if page_content_from_input:
            # Append page_content if it exists, clearly marking it for the agent
            final_agent_input_str += f"\n\n[Context: The user has also provided the following page content to consider for this question]:\n{page_content_from_input}"
    
    elif isinstance(user_input, str):
        final_agent_input_str = user_input
    
    else:
        return "Invalid input type. Please provide a string or a dictionary with 'question' and optionally 'page_content'."

    if not final_agent_input_str.strip(): # Check if effectively empty
        return "Input is empty. Please provide a question."

    agent_payload = {
        "input": final_agent_input_str
    }
    print(f"Agent payload: {agent_payload}")  # Debugging line to see the payload structure
    
    result = SMART_AGENT.invoke(agent_payload)
    return result.get("output", str(result))