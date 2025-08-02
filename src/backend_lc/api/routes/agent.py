from fastapi import APIRouter
from pydantic import BaseModel
from lc.react_agent import run_agent

router = APIRouter()

class AgentQuery(BaseModel):
    input: dict | str

@router.post("/ask")
def ask_agent(query: AgentQuery):
    print("user asked:", query.input)
    
    output_dict = run_agent(query.input)
    
    return {"data": output_dict}