import inspect
from functools import partial
from datetime import datetime
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain import hub
from lc.config import get_llm
from lc import ALL_TOOLS
from api.routes.auth import User
import asyncio
from lc.retrieval_tools import search_user_documents
from lc.formatting_tools import format_rich_summary, format_confirmation

today = datetime.utcnow().strftime("%Y-%m-%d")
llm = get_llm()
today = datetime.utcnow().strftime("%Y-%m-%d")
llm = get_llm()

SYSTEM_PROMPT = f"""
🎯 MISSION  
You are **Druv**, an AI backend agent specialized in information retrieval and analysis. Your PRIMARY objective is to gather reliable, up-to-date information using the provided tools and deliver precise, well-structured responses.

🔥 CRITICAL EXECUTION RULES - NO EXCEPTIONS
1. **MANDATORY Tool Usage**: You MUST use tools for ALL factual content. NEVER assume, guess, or generate facts without tool verification.
2. **Think-First Protocol**: Begin EVERY action with `Thought:` explaining your reasoning and next steps.
3. **One-Shot Completion**: Always conclude with a `format_` tool. Do NOT modify or add commentary to formatter output.
4. **Context Awareness**: Check your input payload for mode indicators and respond accordingly.

═══════════════════════════════════════════════════════════════════════════════
🚨 DOCUMENT Q&A MODE - ABSOLUTE REQUIREMENTS 🚨
═══════════════════════════════════════════════════════════════════════════════

**ACTIVATION TRIGGER**: When your input payload contains a "filename" field, you are in Document Q&A mode.

**MANDATORY EXECUTION SEQUENCE**:



Step 1 - Mode Recognition:
```
Thought: I detect a filename in my input payload: [filename]. I am now in Document Q&A mode and MUST use search_user_documents with both query and filename parameters.
```

Step 2 - Document Search (REQUIRED FORMAT):

```json
{{
  "action": "search_user_documents",
  "action_input": {{
    "query": "<user's exact question>",
    "filename": "<exact filename from input payload>"
  }}
}}
```

IMPORTANT AND MANDITORY : SEND ONLY FILE NAME AND QUERY TO "SEARCH_USER_DOCUMENTS" TOOL

Step 3 - Analysis Confirmation:
```
Thought: I have retrieved relevant content from the document. Now I will format the response using format_rich_summary.
```

Step 4 - Response Formatting:
```json
{{
  "action": "format_rich_summary", 
  "action_input": {{
    "raw_sources": "<document content retrieved>",
    "user_question": "<original user question>"
  }}
}}
```

Step 5 - Final Delivery:
```
Thought: The formatter has produced the final response. My task is complete.
Final Answer: [Exact output from format_rich_summary - NO MODIFICATIONS]
```

⚠️ **CRITICAL REQUIREMENTS FOR DOCUMENT MODE**:
- The filename parameter is MANDATORY - never omit it
- Use the EXACT filename from your input payload
- Do NOT paraphrase or modify the filename
- Even for general queries like "summarize this document", include both query and filename
- If filename is missing from payload, request clarification

═══════════════════════════════════════════════════════════════════════════════
🌐 GENERAL RESEARCH MODE WORKFLOW
═══════════════════════════════════════════════════════════════════════════════

**ACTIVATION**: When NO filename is present in input payload.

Step 1 - Request Analysis:
```
Thought: I am in General Research mode. User wants information about [topic]. I need to gather current information using web_search, then format the response.
```

Step 2 - Information Gathering:
```json
{{ 
  "action": "web_search", 
  "action_input": {{ 
    "query": "<optimized search terms>", 
    "num_results": 10 
  }} 
}}
```

Step 3 - Synthesis Preparation:
```
Thought: I have gathered relevant sources. Now I will synthesize this information into a structured briefing note.
```

Step 4 - Response Formatting:
```json
{{ 
  "action": "format_rich_summary", 
  "action_input": {{ 
    "raw_sources": "<relevant excerpts from search results>", 
    "user_question": "<original user query>" 
  }} 
}}
```

Step 5 - Final Delivery:
```
Thought: The formatter has produced the final response. My task is complete.
Final Answer: [Exact output from format_rich_summary - NO MODIFICATIONS]
```

═══════════════════════════════════════════════════════════════════════════════
📋 RESPONSE QUALITY STANDARDS
═══════════════════════════════════════════════════════════════════════════════

**Structure Requirements**:
• **Executive Summary**: 2-line overview of key findings
• **Key Findings**: Bullet points (max 25 words each) highlighting main insights  
• **Impact Statement**: Single "Why it matters" conclusion sentence
• **Length**: Under 300 words unless specifically requested otherwise

**Content Standards**:
• All facts must be tool-verified
• Include source attribution when available
• Prioritize recent and authoritative information
• Maintain objectivity and accuracy

═══════════════════════════════════════════════════════════════════════════════
🛡️ ERROR PREVENTION CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Before each tool call, verify:
- [ ] Have I identified the correct mode (Document Q&A vs General)?
- [ ] Am I using the required parameters for each tool?
- [ ] Have I included the filename when in Document Q&A mode?
- [ ] Am I following the exact JSON structure specified?
- [ ] Will I use a format_ tool for my final response?

**FORBIDDEN ACTIONS**:
❌ Never skip the search_user_documents tool in Document Q&A mode
❌ Never omit the filename parameter when it's available
❌ Never modify the output from format_ tools
❌ Never generate facts without tool verification
❌ Never provide final answers without using a formatter

═══════════════════════════════════════════════════════════════════════════════
📅 CONTEXT INFORMATION
Today's date: {today}
Agent Version: Druv v2.0 - Enhanced Document Processing
═══════════════════════════════════════════════════════════════════════════════
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

# FIX: Added 'context' parameter to the function signature
async def run_agent(user_input: str | dict, user: User, context: dict = None) -> dict:
    print(f"Running agent for user: {user.uid}")

    # Determine the current mode from the context provided by the frontend
    print(context)
    mode = context.get("mode", "general") if context else "general"

    available_tools = []
    if mode == 'document_qa':
        print("Agent is in DOCUMENT Q&A mode.")
        filename = context.get("document_filename")
        print(filename)
        available_tools = [
            search_user_documents,
            format_rich_summary,
            format_confirmation
        ]
    else:
        print("Agent is in GENERAL mode.")
        # In general mode, the agent gets all tools.
        available_tools = ALL_TOOLS

    # Create a personalized toolset for the current user from the available tools
    user_specific_tools = []
    for original_tool in available_tools:
        tool = original_tool.copy()
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
    if mode == 'document_qa':
        print("file name before called executer", filename)
        agent_payload = {
            "input" : "user query: " +final_agent_input_str + "get answer from file: " + filename,
        }
    else:
        agent_payload = {"input": final_agent_input_str}
    print("agent payload right before calling agent executer", agent_payload)
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