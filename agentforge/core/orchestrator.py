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
        force_agent: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        preferred_model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream the processing of a query, showing the workflow and responses from multiple agents.
        """
        def process_chunk(chunk):
            """Helper function to process chunks that may be dictionaries or JSON strings"""
            if isinstance(chunk, str):
                try:
                    return json.loads(chunk)
                except json.JSONDecodeError:
                    return {"type": "response", "content": chunk, "agent": "system"}
            return chunk

        def get_available_agents():
            """Helper function to get list of available agents"""
            return [
                {
                    "name": agent.name,
                    "description": agent.description,
                    "task_types": agent.config.task_types if hasattr(agent, 'config') else []
                }
                for agent in self.agents
            ]

        if not self.agents:
            yield json.dumps({
                "type": "error",
                "content": "No agents available",
                "available_agents": []
            })
            return

        try:
            if force_agent:
                # Use the specified agent directly
                matching_agents = [a for a in self.agents if a.name.lower() == force_agent.lower()]
                if not matching_agents:
                    yield json.dumps({
                        "type": "error",
                        "content": f"Specified agent '{force_agent}' not found",
                        "available_agents": get_available_agents()
                    })
                    return
                selected_agent = matching_agents[0]
                
                # Stream the selected agent's response
                async for chunk in selected_agent.stream_process(
                    query,
                    temperature=temperature,
                    preferred_model=preferred_model,
                    **kwargs
                ):
                    yield json.dumps(process_chunk(chunk))
                    
            else:
                # Use manager to handle the query
                if not self.manager:
                    yield json.dumps({
                        "type": "error",
                        "content": "Manager Assistant not available",
                        "available_agents": get_available_agents()
                    })
                    return
                
                # Stream manager's response
                async for chunk in self.manager.stream_process(
                    query,
                    temperature=temperature,
                    preferred_model=preferred_model,
                    **kwargs
                ):
                    yield json.dumps(process_chunk(chunk))
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            yield json.dumps({
                "type": "error",
                "content": f"Error in orchestrator: {str(e)}\nDetails: {error_details}",
                "available_agents": get_available_agents()
            })
            
    async def process_query(
        self,
        query: str,
        force_agent: Optional[str] = None,
        temperature: Optional[float] = 0.7,
        preferred_model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Non-streaming version for compatibility"""
        responses = []
        workflow = None
        
        async for chunk in self.stream_process(
            query,
            force_agent=force_agent,
            temperature=temperature,
            preferred_model=preferred_model,
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