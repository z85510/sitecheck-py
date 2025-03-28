from typing import List, Dict, Any, Optional, AsyncGenerator
from .base_agent import BaseAgent
from ..agents.manager_assistant import ManagerAssistant
from ..assistants.configs.assistant_configs import get_all_assistants
import json
import traceback
import logging

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ):
        """Initialize the orchestrator with API keys.
        
        Args:
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            base_path: Base path for document storage
        """
        self.base_path = base_path
        self.api_keys = {
            "openai": openai_api_key,
            "anthropic": anthropic_api_key
        }
        
        # Initialize manager agent
        self.manager_agent = ManagerAssistant(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )
        
        # Initialize agent registry
        self.agents = {}
        self._load_agents()

    def _load_agents(self):
        """Load all available agents from configurations."""
        try:
            # Get all assistant configurations
            assistant_configs = get_all_assistants()
            
            # Initialize each assistant as an agent
            for config in assistant_configs:
                # Use name as ID if not explicitly provided
                agent_id = config.get("id", config.get("name", "")).lower().replace(" ", "_")
                if not agent_id:
                    logger.warning(f"Skipping assistant config without name or id: {config}")
                    continue
                    
                if agent_id not in self.agents:
                    agent = self.manager_agent.create_assistant(
                        config,
                        openai_api_key=self.api_keys["openai"],
                        anthropic_api_key=self.api_keys["anthropic"],
                        base_path=self.base_path
                    )
                    self.agents[agent_id] = agent
                    
            logger.info(f"Loaded {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Error loading agents: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def process_query(
        self,
        query: str,
        agent_name: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Process a query and return a response (non-streaming)."""
        response_chunks = []
        async for chunk in self.stream_process(
            query=query,
            agent_name=agent_name,
            temperature=temperature,
            **kwargs
        ):
            if chunk["type"] == "content":
                response_chunks.append(chunk["content"])
        
        return "".join(response_chunks)

    async def stream_process(
        self,
        query: str,
        agent_name: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a query with streaming response."""
        try:
            # If specific agent requested, use it directly
            if agent_name:
                agent = self.get_agent(agent_name)
                if not agent:
                    yield {
                        "type": "error",
                        "content": f"Agent '{agent_name}' not found"
                    }
                    return
                
                yield {
                    "type": "status",
                    "content": f"Using specified agent: {agent_name}"
                }
                
                async for chunk in agent.stream_process(
                    query=query,
                    temperature=temperature,
                    **kwargs
                ):
                    yield chunk
                return
            
            # Otherwise, use manager agent to coordinate
            yield {
                "type": "status",
                "content": "Analyzing query and selecting appropriate agents..."
            }
            
            async for chunk in self.manager_agent.stream_process(
                query=query,
                temperature=temperature,
                **kwargs
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in stream_process: {str(e)}")
            logger.error(traceback.format_exc())
            yield {
                "type": "error",
                "content": str(e)
            }

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get an agent by name."""
        # Try different name formats
        name_variations = [
            agent_name,
            agent_name.lower(),
            agent_name.title(),
            agent_name.lower().replace(" ", "_"),
            agent_name.lower().replace("_", " ").title()
        ]
        
        for name in name_variations:
            # Check in agents dictionary
            if name in self.agents:
                return self.agents[name]
            
            # Check by agent display name
            for agent in self.agents.values():
                if agent.name.lower() == name.lower():
                    return agent
        
        return None

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents with their details."""
        return [
            {
                "id": agent_id,
                "name": agent.name,
                "description": agent.description,
                "expertise": getattr(agent, "expertise", []),
                "capabilities": getattr(agent, "capabilities", [])
            }
            for agent_id, agent in self.agents.items()
        ]

    def add_agent(self, agent: BaseAgent) -> None:
        """Add a new agent to the orchestrator."""
        agent_id = agent.name.lower().replace(" ", "_")
        self.agents[agent_id] = agent
        
        # Set API keys for the agent if needed
        if hasattr(agent, "model_manager"):
            if self.api_keys["openai"]:
                agent.model_manager.set_api_key("openai", self.api_keys["openai"])
            if self.api_keys["anthropic"]:
                agent.model_manager.set_api_key("anthropic", self.api_keys["anthropic"])

    def remove_agent(self, agent_name: str) -> None:
        """Remove an agent from the orchestrator."""
        agent = self.get_agent(agent_name)
        if agent:
            agent_id = agent.name.lower().replace(" ", "_")
            if agent_id in self.agents:
                del self.agents[agent_id] 