import os
import json
import logging
import traceback
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, WebSocket, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .core.orchestrator import AgentOrchestrator
from agentforge.assistants.configs.assistant_configs import get_all_assistants

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API keys from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
base_path = os.getenv("VECTORDB_PATH", "agentforge")

if not openai_api_key or not anthropic_api_key:
    raise ValueError("Missing required API keys")

# Initialize orchestrator with API keys
orchestrator = AgentOrchestrator(
    openai_api_key=openai_api_key,
    anthropic_api_key=anthropic_api_key
)

# Create FastAPI app
app = FastAPI(
    title="SiteCheck AI API",
    description="AI-powered construction safety and management API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    text: str
    temperature: Optional[float] = Field(
        0.7,
        description="Temperature for model response (0.0 to 1.0)", 
        ge=0.0, 
        le=1.0
    )
    agent_name: Optional[str] = Field(
        None,
        description="Specific agent to handle the query"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "What are the safety requirements for working at heights?",
                "temperature": 0.7,
                "agent_name": None
            }
        }

class AssistantInfo(BaseModel):
    name: str
    role: str
    description: str
    expertise: List[str]

async def stream_generator(query: str, temperature: float = 0.7, agent_name: Optional[str] = None):
    """Generate streaming response chunks."""
    try:
        async for chunk in orchestrator.stream_process(
            query=query,
            agent_name=agent_name,
            temperature=temperature
        ):
            # Ensure chunk is a dictionary
            if not isinstance(chunk, dict):
                logger.warning(f"Received non-dict chunk: {chunk}")
                continue

            # Format chunk for SSE based on type
            chunk_type = chunk.get("type", "unknown")
            
            if chunk_type == "status":
                data = {
                    'type': 'status',
                    'content': chunk.get('content', ''),
                    'details': chunk.get('details', {})
                }
                yield f"data: {json.dumps(data)}\n\n"
                
            elif chunk_type == "content":
                data = {
                    'type': 'content',
                    'content': chunk.get('content', ''),
                    'agent': chunk.get('agent', None)
                }
                yield f"data: {json.dumps(data)}\n\n"
                
            elif chunk_type == "thinking":
                data = {
                    'type': 'thinking',
                    'content': chunk.get('message', ''),
                    'details': chunk.get('details', {})
                }
                yield f"data: {json.dumps(data)}\n\n"
                
            elif chunk_type == "error":
                data = {
                    'type': 'error',
                    'content': chunk.get('content', str(chunk.get('error', 'Unknown error')))
                }
                yield f"data: {json.dumps(data)}\n\n"
                
            elif chunk_type == "workflow":
                data = {
                    'type': 'workflow',
                    'step': chunk.get('step', ''),
                    'content': chunk.get('content', '')
                }
                yield f"data: {json.dumps(data)}\n\n"
                
            else:
                # For any other chunk types, pass through as is
                yield f"data: {json.dumps(chunk)}\n\n"
                
        # Send completion message
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in stream_generator: {str(e)}")
        logger.error(traceback.format_exc())
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

@app.post("/query")
async def process_query(request: QueryRequest) -> Dict[str, Any]:
    """Process a query and return a response."""
    try:
        response = await orchestrator.process_query(
            query=request.text,
            agent_name=request.agent_name,
            temperature=request.temperature
        )
        return {"response": response}
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {"error": str(e)}

@app.post("/stream_process")
async def stream_process(request: QueryRequest):
    """Process a query with streaming response."""
    return StreamingResponse(
        stream_generator(
            query=request.text,
            temperature=request.temperature,
            agent_name=request.agent_name
        ),
        media_type="text/event-stream"
    )

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/assistants")
async def list_assistants() -> Dict[str, Any]:
    """List all available assistants."""
    try:
        assistants = orchestrator.list_agents()
        return {"assistants": assistants}
    except Exception as e:
        logger.error(f"Error listing assistants: {str(e)}")
        return {"error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming responses."""
    await websocket.accept()
    try:
        while True:
            # Receive and validate request
            data = await websocket.receive_json()
            request = QueryRequest(**data)
            
            async for chunk in orchestrator.stream_process(
                query=request.text,
                agent_name=request.agent_name,
                temperature=request.temperature
            ):
                await websocket.send_json(chunk)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_json({"type": "error", "error": str(e)})
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 