# lc/react_agent.py
# Note: Other imports and functions remain the same. This focuses on the prompt fix.

from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain import hub
from lc.config import get_llm
from lc import ALL_TOOLS
from datetime import datetime

today = datetime.utcnow().strftime("%Y-%m-%d")
llm = get_llm()

# --- THIS IS THE FIX ---
# The SYSTEM_PROMPT is now extremely strict about the Final Answer format.

SYSTEM_PROMPT = """
# MISSION
Your mission is to act as Druv, a proactive and intelligent AI personal assistant. Your primary goal is to use tools to gather information and then format that information into a structured JSON object for the frontend application.
# TOOL USAGE PROTOCOL
**RULE 1: ALWAYS SEARCH FIRST FOR FACTUAL QUERIES**
For any question that requires current, factual, or specific information (e.g., news, events, technical details, statistics), you **MUST** use the `web_search` tool. **DO NOT** answer from your internal knowledge.

**RULE 2: ALWAYS FORMAT AFTER SEARCHING**
After using `web_search`, you **MUST** use the `format_web_summary` tool to structure the raw text before giving the `Final Answer`.

# CRITICAL RESPONSE PROTOCOL - YOU MUST FOLLOW THIS EXACTLY
⚠️  **MANDATORY**: EVERY response must start with "Thought:" - NO EXCEPTIONS.
⚠️  **MANDATORY**: After your thought, you MUST use either an "Action" or a "Final Answer".

---
### FORMAT 1: Using a Tool
Use this format to call any tool, including a formatting tool.
Thought: [Your step-by-step reasoning for using a specific tool.]
Action:
```json
{{
  "action": "tool_name",
  "action_input": {{ "arg_name": "value" }}
}}
```

---
### FORMAT 2: The Final Answer
The Final Answer is your last step. Its format is NOT flexible.

**RULE 1: DATA-BASED ANSWERS MUST BE JSON**
If your answer is based on data returned from ANY tool (like calendar events, search results, etc.), the `Final Answer` **MUST** be the JSON object produced by a `format_` tool.

**RULE 2: CONVERSATIONAL ANSWERS ARE RARE**
The ONLY time you should provide a simple string in `Final Answer` is for a direct greeting (e.g., "Hi, how can I help?") or if you cannot use any tools to answer the user's question.

---
# MANDATORY WORKFLOW & EXAMPLES

### Correct Workflow (Querying Data):
1.  **Thought:** I need to get the user's calendar events.
2.  **Action:** Use `get_events_on_date`.
3.  **(Tool returns raw data: `{{'status': '...', 'events': [...]}}`)**
4.  **Thought:** I have the raw event data. Now I must format it for the UI using the `format_calendar_view` tool. The output of this tool will be my final answer.
5.  **Action:** Use `format_calendar_view`.
6.  **(Tool returns structured JSON: `{{"response_type":"calendar_view",...}}`)**
7.  **Thought:** I have received the structured JSON from the formatting tool. This IS the final answer. I must stop here.
8.  **Final Answer:** `{{"response_type":"calendar_view", "events": [...]}}`

### **INCORRECT** Workflow (What NOT to do):
1.  ...steps 1-7 are correct...
2.  **Thought:** I have the JSON, now I will write a nice sentence about it. **<-- THIS IS WRONG!**
3.  **Final Answer:** "You have 2 events today..." **<-- THIS IS FORBIDDEN!**

# CONTEXT
Today's Date: {today}

⚠️  REMEMBER: Your primary job is to provide structured JSON. Do not add conversational text after you have successfully formatted the data.
"""


# The rest of your file remains the same...

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

# This error handler is still useful for other potential issues
def fix_parsing_error(error):
    error_str = str(error)
    if "Could not parse LLM output:" in error_str:
        actual_response = error_str.split("Could not parse LLM output:")[-1].strip()
        return actual_response
    return "I encountered a formatting issue. Please try again."

SMART_AGENT = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=ALL_TOOLS,
    verbose=True,
    handle_parsing_errors=fix_parsing_error,
)

# In lc/react_agent.py

def run_agent(user_input: str | dict) -> dict:
    """
    Runs the agent and returns a dictionary containing both the final answer
    and the intermediate reasoning steps.
    """
    final_agent_input_str = ""
    if isinstance(user_input, dict):
        question = user_input.get("question")
        page_content = user_input.get("page_content")
        final_agent_input_str = question
        if page_content:
            final_agent_input_str += f"\n\n[Context from current page]:\n{page_content}"
    else:
        final_agent_input_str = user_input

    agent_payload = {"input": final_agent_input_str}
    
    # Execute the agent, asking it to return the intermediate steps
    result = SMART_AGENT.invoke(agent_payload, return_intermediate_steps=True)

    # Format the response for the frontend
    final_response = {
        "final_answer": result.get("output"),
        "reasoning_trace": []
    }

    if "intermediate_steps" in result:
        for step in result["intermediate_steps"]:
            action, observation = step
            final_response["reasoning_trace"].append({
                "tool": action.tool,
                "tool_input": action.tool_input,
                "observation": str(observation)
            })

    return final_response
