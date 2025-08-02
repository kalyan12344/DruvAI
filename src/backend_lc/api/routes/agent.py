from fastapi import APIRouter, Depends
from pydantic import BaseModel
from lc.react_agent import run_agent
from api.routes.auth import User, get_current_user

router = APIRouter()

class AgentQuery(BaseModel):
    input: dict | str

@router.post("/ask")
async def ask_agent(query: AgentQuery, current_user: User = Depends(get_current_user)):
    output_dict = await run_agent(user_input=query.input, user=current_user)
    return output_dict