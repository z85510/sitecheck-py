import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import json

from .core.orchestrator import AgentOrchestrator
from .agents.construction_coordinator import ConstructionCoordinator
from .agents.construction_meeting import ConstructionMeeting
from .agents.general_assistant import GeneralAssistant

# Load environment variables
load_dotenv()

app = FastAPI(title="AgentForge", description="An agentic system with multiple specialized AI assistants")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API keys from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

if not openai_api_key or not anthropic_api_key:
    raise ValueError("Missing required API keys")

# Initialize agents
coordinator = ConstructionCoordinator(
    openai_api_key=openai_api_key,
    anthropic_api_key=anthropic_api_key
)

meeting = ConstructionMeeting(
    openai_api_key=openai_api_key,
    anthropic_api_key=anthropic_api_key
)

general = GeneralAssistant(
    openai_api_key=openai_api_key,
    anthropic_api_key=anthropic_api_key
)

# Initialize orchestrator with agents and API keys
orchestrator = AgentOrchestrator(
    agents=[coordinator, meeting, general],
    openai_api_key=openai_api_key,
    anthropic_api_key=anthropic_api_key
)

class QueryRequest(BaseModel):
    query: str
    force_agent: Optional[str] = None
    temperature: Optional[float] = 0.7

@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        async def generate_response():
            async for chunk in orchestrator.stream_process(
                query=request.query,
                force_agent=request.force_agent,
                temperature=request.temperature
            ):
                yield chunk + "\n"
                
        return StreamingResponse(
            generate_response(),
            media_type="application/x-ndjson"
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/agents")
async def list_agents():
    """
    List all available agents and their descriptions.
    """
    return {
        "agents": [
            {
                "name": agent.name,
                "description": agent.description,
                "task_types": agent.config.task_types if hasattr(agent, 'config') else None,
                "keywords": agent.config.keywords if hasattr(agent, 'config') else None
            }
            for agent in orchestrator.agents
        ]
    } 