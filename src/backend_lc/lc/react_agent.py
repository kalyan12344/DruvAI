import inspect
from functools import partial
from datetime import datetime
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain import hub
from lc.config import get_llm
from lc import ALL_TOOLS
from api.routes.auth import User
import asyncio

today = datetime.utcnow().strftime("%Y-%m-%d")
llm = get_llm()
today = datetime.utcnow().strftime("%Y-%m-%d")
llm = get_llm()

SYSTEM_PROMPT = """
MISSION  
You are **Druv**, an AI research analyst. Your task is to gather reliable, up-to-date information with the provided tools and craft a concise, well-structured Briefing Note using the `format_rich_summary` tool.

CORE RULES  
1. *Think aloud*: begin every reasoning step with **Thought:** explaining why you will (or won’t) take an action.  
2. *Tool-first facts*: never rely on memory; all factual content must come from a tool call.  
3. *One-shot finish*: whatever the `format_…` tool returns is the Final Answer—do not alter or add commentary.

STANDARD WORKFLOW  
Step 1 – Clarify  
Thought: Restate the user’s request and list the sub-topics or keywords you need.  

Step 2 – Collect sources  
Thought: Decide the search terms.  
Action:  
```json
{{ "action": "web_search",
  "action_input": {{ "query": "<keywords>", "num_results": 10 }}}}
Step 3 – Fill gaps (optional)
Thought: If coverage is incomplete, run additional targeted searches.

Step 4 – Synthesize
Thought: Ready to draft the briefing.
Action:

json
Copy
Edit
{ "action": "format_rich_summary",
  "action_input": {
    "raw_sources": "<excerpts or full text>",
    "user_question": "<original query>"
  }}
Step 5 – Deliver
Thought: Formatter returned the Briefing Note; my work is complete.
Final Answer: <exact output from format_rich_summary>

TOOL CALL EXAMPLE
Thought: Need latest AI-hardware news.
Action:

json
Copy
Edit
{{ "action": "web_search",
  "action_input": {{ "query": "latest ai hardware news august 2025", "num_results": 10 }}}}
STYLE NOTES
• Start the Briefing Note with a two-sentence executive summary.
• Follow with bulleted key findings, each ≤ 25 words.
• End with a single “Why it matters” line.
• Length ≤ 300 words unless user requests more detail.

CONTEXT
Today’s date: {today}


""" 


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
    prompt=custom_prompt,
    # output_parser=ReActSingleInputOutputParser(require_thought=True) 

)

def fix_parsing_error(error):
    error_str = str(error)
    if "Could not parse LLM output:" in error_str:
        return error_str.split("Could not parse LLM output:")[-1].strip()
    return "I encountered a formatting issue. Please try again."

async def run_agent(user_input: str | dict, user: User) -> dict:
    user_specific_tools = []
    for original_tool in ALL_TOOLS:
        tool = original_tool.copy()
        
        # --- THIS IS THE FIX ---
        # Add a check to ensure the tool's function is valid before using it.
        if not callable(getattr(tool, 'func', None)):
            print(f"🔥 CRITICAL ERROR: The tool '{getattr(tool, 'name', 'Unnamed Tool')}' is invalid or has no function.")
            # Skip this invalid tool to prevent a crash
            continue
        # --- END OF FIX ---

        tool_params = inspect.signature(tool.func).parameters
        if 'user_id' in tool_params:
            tool.func = partial(tool.func, user_id=user.uid)
        elif 'user_email' in tool_params:
            tool.func = partial(tool.func, user_email=user.email)
        
        user_specific_tools.append(tool)

    agent = create_structured_chat_agent(
        llm=llm,
        tools=user_specific_tools,
        prompt=custom_prompt
    )
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=user_specific_tools,
        verbose=True,
        handle_parsing_errors=fix_parsing_error,
    )
    
    final_agent_input_str = user_input if isinstance(user_input, str) else user_input.get("question", "")
    agent_payload = {"input": final_agent_input_str}
    result = await agent_executor.ainvoke(agent_payload, return_intermediate_steps=True)
    
    final_response = {"output": result.get("output"), "intermediate_steps": []}
    if "intermediate_steps" in result:
        for step in result["intermediate_steps"]:
            action, observation = step
            thought = action.log.split("Action:")[0].replace("Thought:", "").strip()
            final_response["intermediate_steps"].append({
                "thought": thought, "tool": action.tool,
                "tool_input": action.tool_input, "observation": str(observation)
            })
    return final_response