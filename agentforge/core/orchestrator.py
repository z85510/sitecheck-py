from typing import List, Dict, Any, Optional, AsyncGenerator
from .base_agent import BaseAgent
from ..agents.manager_assistant import ManagerAssistant
import json

class AgentOrchestrator:
    def __init__(self, agents: List[BaseAgent], openai_api_key: Optional[str] = None, anthropic_api_key: Optional[str] = None):
        """Initialize the orchestrator with a list of agents and optional API keys."""
        self.agents = agents
        self.manager = ManagerAssistant(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key
        ) if openai_api_key else None
        
    def add_agent(self, agent: BaseAgent) -> None:
        """Add a new agent to the orchestrator."""
        self.agents.append(agent)
        
    def remove_agent(self, agent_name: str) -> None:
        """Remove an agent from the orchestrator by name."""
        self.agents = [agent for agent in self.agents if agent.name != agent_name]
        
    async def stream_process(
        self,
        query: str,
        agent_name: str,
        temperature: Optional[float] = None,
        preferred_model: Optional[str] = None,
        model_type: Optional[str] = None,
        model_category: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a query with a specific agent and stream the response."""
        try:
            # Get the agent instance
            agent = self.get_agent(agent_name)
            if not agent:
                available_agents = self.list_agents()
                yield {
                    "type": "error",
                    "content": f"Agent '{agent_name}' not found. Available agents: {', '.join(available_agents)}",
                    "agent": "orchestrator"
                }
                return

            # Stream response from agent
            async for chunk in agent.stream_process(
                query=query,
                temperature=temperature,
                preferred_model=preferred_model,
                model_type=model_type,
                model_category=model_category,
                **kwargs
            ):
                yield chunk

        except Exception as e:
            yield {
                "type": "error",
                "content": f"Error in orchestrator: {str(e)}",
                "agent": "orchestrator"
            }
            
    async def process_query(
        self,
        query: str,
        agent_name: str,
        temperature: Optional[float] = None,
        preferred_model: Optional[str] = None,
        model_type: Optional[str] = None,
        model_category: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Non-streaming version for compatibility"""
        responses = []
        workflow = None
        
        async for chunk in self.stream_process(
            query=query,
            agent_name=agent_name,
            temperature=temperature,
            preferred_model=preferred_model,
            model_type=model_type,
            model_category=model_category,
            **kwargs
        ):
            if chunk["type"] == "response":
                responses.append(chunk["content"])
            elif chunk["type"] == "workflow":
                workflow = chunk["content"]["workflow"]
        
        return {
            "response": "".join(responses),
            "workflow": workflow
        } 