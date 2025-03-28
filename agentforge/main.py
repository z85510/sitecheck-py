import os
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json
import logging
import traceback

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str
    agent: str = Field(
        default="General Assistant",  # Default to "General Assistant" to match actual agent name
        description="""Agent name to handle the query. Available agents:
        - General Assistant: General purpose AI assistant
        - Construction Meeting Assistant: Construction meeting specialist
        - Safety Assistant: Safety and compliance specialist
        """
    )
    temperature: Optional[float] = Field(
        0.7,  # Default temperature
        description="Temperature for model response (0.0 to 1.0)", 
        ge=0.0, 
        le=1.0
    )
    preferred_model: Optional[str] = Field(
        "gpt-4o-mini",  # Default to gpt-4o-mini
        description="""Model to use for the response. Examples:
        - gpt-4o-mini: Default OpenAI model (cost-optimized)
        - o3-mini: Claude 3 Opus (reasoning)
        - gpt-4o: GPT-4 Turbo (flagship)
        """
    )
    model_type: Optional[str] = Field(
        "default",  # Default to "default" type
        description="Type of model to use ('reasoning' or 'default')"
    )
    model_category: Optional[str] = Field(
        "cost-optimized",  # Default to cost-optimized category
        description="""Category of model to use:
        - reasoning: Best for complex analysis
        - flagship: Best quality but expensive
        - cost-optimized: Good balance of quality and cost
        - legacy: Older models
        - claude: Anthropic models
        """
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Hello",  # Simple example
                "agent": "General Assistant"  # Match exact agent name
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
    
    Minimal example:
    ```json
    {
        "query": "Hello"
    }
    ```
    
    Full example:
    ```json
    {
        "query": "Create a safety meeting agenda",
        "agent": "General Assistant",
        "temperature": 0.7,
        "preferred_model": "gpt-4o-mini",
        "model_type": "reasoning",
        "model_category": "flagship"
    }
    ```
    """
)
async def process_query(request: QueryRequest):
    try:
        logger.info(f"Received query request: {request.dict()}")
        
        # Get available agents with both exact names and normalized names
        available_agents = {}
        normalized_to_actual = {}
        for agent in orchestrator.agents:
            # Store both the exact name and normalized versions
            available_agents[agent.name] = agent.name  # Exact match
            available_agents[agent.name.lower()] = agent.name  # Lowercase
            available_agents[agent.name.lower().replace(" ", "_")] = agent.name  # Snake case
            available_agents[agent.name.lower().replace(" ", "")] = agent.name  # No spaces
            normalized_to_actual[agent.name.lower()] = agent.name
            
        logger.debug(f"Available agents mapping: {available_agents}")
        
        # Try different variations of the agent name
        agent_variations = [
            request.agent,  # Original
            request.agent.lower(),  # Lowercase
            request.agent.lower().replace(" ", "_"),  # Snake case
            request.agent.lower().replace(" ", ""),  # No spaces
            request.agent.title()  # Title case
        ]
        
        # Find the first matching variation
        actual_agent_name = None
        for variation in agent_variations:
            if variation in available_agents:
                actual_agent_name = available_agents[variation]
                break
                
        if not actual_agent_name:
            logger.warning(f"Agent not found: {request.agent}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Agent '{request.agent}' not found",
                    "available_agents": list(normalized_to_actual.values()),
                    "suggestion": "Use one of the available agent names listed above."
                }
            )
        
        logger.info(f"Using agent: {actual_agent_name}")
        
        # Log model selection
        logger.info(f"Model settings: type={request.model_type}, category={request.model_category}, model={request.preferred_model}")
        
        # Process the query
        try:
            response = await orchestrator.process_query(
                query=request.query,
                agent_name=actual_agent_name,  # Use the correct case-sensitive name
                temperature=request.temperature,
                preferred_model=request.preferred_model,
                model_type=request.model_type,
                model_category=request.model_category
            )
            
            logger.debug(f"Raw response: {response}")
            
            if not response:
                logger.error(f"Empty response from agent {actual_agent_name}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Agent returned an empty response",
                        "agent": actual_agent_name,
                        "query": request.query,
                        "model": request.preferred_model
                    }
                )
                
            if isinstance(response, dict) and not any(response.values()):
                logger.error(f"Empty dictionary response from agent {actual_agent_name}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Agent returned an empty dictionary",
                        "agent": actual_agent_name,
                        "query": request.query,
                        "model": request.preferred_model,
                        "response": response
                    }
                )
                
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"Error processing query: {str(e)}",
                    "agent": actual_agent_name,
                    "query": request.query,
                    "model": request.preferred_model,
                    "traceback": traceback.format_exc()
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "available_agents": [agent.name for agent in orchestrator.agents],
                "note": "Use one of the available agent names listed above.",
                "traceback": traceback.format_exc()
            }
        )

@app.post("/stream_process",
    response_class=StreamingResponse,
    summary="Stream process a query with a specific agent",
    description="""
    Send a query to a specific agent and get a streaming response.
    
    Example request (minimal):
    ```json
    {
        "query": "Hello",
        "agent": "General Assistant"
    }
    ```
    
    Example request (with model preferences):
    ```json
    {
        "query": "Create a safety meeting agenda",
        "agent": "General Assistant",
        "temperature": 0.7,
        "preferred_model": "o3-mini",
        "model_type": "reasoning",
        "model_category": "flagship"
    }
    ```
    
    Available agents:
    - General Assistant: General purpose AI assistant
    - Construction Meeting Assistant: Construction meeting specialist
    - Safety Assistant: Safety and compliance specialist
    """
)
async def stream_process(request: QueryRequest):
    try:
        logger.info(f"Received stream request: {request.dict()}")
        
        # Get available agents with both exact names and normalized names
        available_agents = {}
        normalized_to_actual = {}
        for agent in orchestrator.agents:
            # Store both the exact name and normalized versions
            available_agents[agent.name] = agent.name  # Exact match
            available_agents[agent.name.lower()] = agent.name  # Lowercase
            available_agents[agent.name.lower().replace(" ", "_")] = agent.name  # Snake case
            available_agents[agent.name.lower().replace(" ", "")] = agent.name  # No spaces
            normalized_to_actual[agent.name.lower()] = agent.name
            
        logger.debug(f"Available agents mapping: {available_agents}")
        
        # Try different variations of the agent name
        agent_variations = [
            request.agent,  # Original
            request.agent.lower(),  # Lowercase
            request.agent.lower().replace(" ", "_"),  # Snake case
            request.agent.lower().replace(" ", ""),  # No spaces
            request.agent.title()  # Title case
        ]
        
        # Find the first matching variation
        actual_agent_name = None
        for variation in agent_variations:
            if variation in available_agents:
                actual_agent_name = available_agents[variation]
                break
                
        if not actual_agent_name:
            logger.warning(f"Agent not found: {request.agent}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": f"Agent '{request.agent}' not found",
                    "available_agents": list(normalized_to_actual.values()),
                    "suggestion": "Use one of the available agent names listed above."
                }
            )
            
        logger.info(f"Using agent: {actual_agent_name}")
        
        # Log model selection
        logger.info(f"Model settings: type={request.model_type}, category={request.model_category}, model={request.preferred_model}")
        
        async def generate_sse():
            try:
                async for chunk in orchestrator.stream_process(
                    query=request.query,
                    agent_name=actual_agent_name,  # Use the correct case-sensitive name
                    temperature=request.temperature,
                    preferred_model=request.preferred_model,
                    model_type=request.model_type,
                    model_category=request.model_category
                ):
                    # Format as SSE
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                error_data = {
                    "type": "error",
                    "content": str(e),
                    "agent": actual_agent_name
                }
                yield f"data: {json.dumps(error_data)}\n\n"
            finally:
                # Send end of stream marker
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_sse(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "available_agents": list(normalized_to_actual.values()),
                "note": "Use one of the available agent names listed above.",
                "traceback": traceback.format_exc()
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