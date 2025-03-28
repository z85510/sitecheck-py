import os
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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
    temperature: Optional[float] = Field(None, description="Temperature for model response (0.0 to 1.0)", ge=0.0, le=1.0)
    preferred_model: Optional[str] = Field(None, description="Preferred model to use (e.g., 'o3-mini', 'gpt-4o')")
    model_type: Optional[str] = Field(None, description="Type of model to use ('reasoning' or 'default')")
    model_category: Optional[str] = Field(None, description="Category of model ('reasoning', 'flagship', 'cost-optimized', 'legacy', 'claude')")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Create a safety meeting agenda",
                "agent": "construction_meeting",
                "temperature": 0.7,
                "model_type": "reasoning",
                "model_category": "flagship"
            }
        }

class AgentInfo(BaseModel):
    name: str
    description: str
    task_types: List[str]

@app.post("/query", 
    response_model=Dict[str, Any],
    summary="Process a query and return the response",
    description="""
    Send a query to a specific agent and get a complete response.
    
    Available agents can be found using the /agents endpoint.
    Available models can be found using the /models endpoint.
    
    Example request:
    ```json
    {
        "query": "Create a safety meeting agenda",
        "agent": "construction_meeting",
        "temperature": 0.7,
        "model_type": "reasoning",
        "model_category": "flagship"
    }
    ```
    """
)
async def process_query(request: QueryRequest):
    try:
        return await orchestrator.process_query(
            query=request.query,
            agent_name=request.agent,
            temperature=request.temperature,
            preferred_model=request.preferred_model,
            model_type=request.model_type,
            model_category=request.model_category
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e),
                "available_agents": [agent.name for agent in orchestrator.agents]
            }
        )

@app.post("/stream_process",
    response_class=StreamingResponse,
    summary="Stream process a query with a specific agent",
    description="""
    Send a query to a specific agent and get a streaming response.
    
    Available agents can be found using the /agents endpoint.
    Available models can be found using the /models endpoint.
    
    Example request:
    ```json
    {
        "query": "Create a safety meeting agenda",
        "agent": "construction_meeting",
        "temperature": 0.7,
        "model_type": "reasoning",
        "model_category": "flagship"
    }
    ```
    """
)
async def stream_process(request: QueryRequest):
    try:
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
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e),
                "available_agents": [agent.name for agent in orchestrator.agents]
            }
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

@app.get("/agents", 
    response_model=List[AgentInfo],
    summary="List available agents",
    description="""
    Returns a list of all available agents and their capabilities.
    
    Each agent has:
    - name: Unique identifier for the agent
    - description: Brief description of the agent's purpose
    - task_types: List of task types the agent can handle
    
    Example response:
    ```json
    [
        {
            "name": "construction_meeting",
            "description": "Specialized assistant for construction meeting management",
            "task_types": ["meeting_agenda", "safety_planning", "progress_tracking"]
        },
        {
            "name": "construction_coordinator",
            "description": "Coordinates construction project activities",
            "task_types": ["project_planning", "resource_management", "scheduling"]
        }
    ]
    ```
    """
)
def list_agents():
    """List available agents and their capabilities"""
    try:
        # Convert agents directly to a list of AgentInfo objects
        agents = [
            AgentInfo(
                name=agent.name,
                description=agent.description,
                task_types=list(set(agent.task_types))  # Remove duplicates from task_types
            )
            for agent in orchestrator.agents
        ]
        
        if not agents:
            raise HTTPException(
                status_code=404,
                detail="No agents available in the system"
            )
            
        return agents
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving agents: {str(e)}"
        )

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