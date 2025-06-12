from fastapi import APIRouter
from pydantic import BaseModel
from lc.react_agent import run_agent


router = APIRouter()

class AgentQuery(BaseModel):
    input: dict | str   
    # tabId: int | None = None

@router.post("/ask")
def ask_agent(query: AgentQuery):
    # run_agent already extracts the string output
    output_string = run_agent(query.input)
    return {"response": output_string} # Use the string directly