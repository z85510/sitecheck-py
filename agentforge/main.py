import os
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import json

from .core.orchestrator import AgentOrchestrator
from .agents.construction_coordinator import ConstructionCoordinator
from .agents.construction_meeting import ConstructionMeeting
from .agents.general_assistant import GeneralAssistant
from .agents import get_all_agents

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
base_path = os.getenv("VECTORDB_PATH", "agentforge")

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
    agents=get_all_agents(
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        base_path=base_path
    ),
    openai_api_key=openai_api_key,
    anthropic_api_key=anthropic_api_key
)

class QueryRequest(BaseModel):
    query: str
    agent: str
    temperature: Optional[float] = None
    preferred_model: Optional[str] = None
    model_type: Optional[str] = None
    model_category: Optional[str] = None

class AgentInfo(BaseModel):
    name: str
    description: str
    task_types: List[str]

@app.post("/query")
async def process_query(request: QueryRequest):
    """Process a query and return the response"""
    return await orchestrator.process_query(
        query=request.query,
        agent_name=request.agent,
        temperature=request.temperature,
        preferred_model=request.preferred_model,
        model_type=request.model_type,
        model_category=request.model_category
    )

@app.post("/stream_process")
async def stream_process(request: QueryRequest):
    """Stream process a query with a specific agent."""
    return StreamingResponse(
        orchestrator.stream_process(
            query=request.query,
            agent_name=request.agent,
            temperature=request.temperature,
            preferred_model=request.preferred_model,
            model_type=request.model_type,
            model_category=request.model_category
        ),
        media_type="text/event-stream"
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Stream responses through WebSocket"""
    await websocket.accept()
    
    try:
        while True:
            # Receive and parse request
            data = await websocket.receive_text()
            request = QueryRequest.parse_raw(data)
            
            # Stream response
            async for chunk in orchestrator.stream_process(
                query=request.query,
                agent_name=request.agent,
                temperature=request.temperature,
                preferred_model=request.preferred_model,
                model_type=request.model_type,
                model_category=request.model_category
            ):
                await websocket.send_text(chunk)
                
    except Exception as e:
        await websocket.send_text(
            json.dumps({
                "type": "error",
                "content": f"WebSocket error: {str(e)}"
            })
        )
    finally:
        await websocket.close()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/agents", response_model=List[AgentInfo])
def list_agents():
    """List available agents and their capabilities"""
    return {
        "agents": [
            {
                "name": agent.name,
                "description": agent.description,
                "task_types": agent.task_types
            }
            for agent in orchestrator.agents
        ]
    }

@app.get("/models")
def list_models():
    """List available models and their capabilities"""
    # Get model manager from first agent (they all share the same instance)
    if not orchestrator.agents:
        return {"models": []}
        
    model_manager = orchestrator.agents[0].model_manager
    return {
        "models": [
            {
                "name": name,
                "alias": specs.get("alias", None),
                "provider": specs["provider"],
                "capabilities": specs["capabilities"],
                "max_tokens": specs["max_tokens"],
                "temperature_range": specs["temperature_range"]
            }
            for name, specs in model_manager.models.items()
        ],
        "aliases": model_manager.model_aliases
    } 