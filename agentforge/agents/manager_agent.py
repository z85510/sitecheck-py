from typing import Dict, Any, List, AsyncGenerator, Optional
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from ..core.base_agent import BaseAgent
import json

class ManagerAgent(BaseAgent):
    def __init__(self, openai_api_key: Optional[str] = None, anthropic_api_key: Optional[str] = None):
        super().__init__(
            name="Construction Manager Assistant",
            description="Manages and coordinates specialized AI assistants",
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key
        )
        self.openai_client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None
        self.anthropic_client = AsyncAnthropic(api_key=anthropic_api_key) if anthropic_api_key else None
        
        if not self.openai_client and not self.anthropic_client:
            raise ValueError("At least one of OpenAI or Anthropic API key must be provided")
        
    async def analyze_query(
        self,
        query: str,
        available_agents: List[Dict[str, Any]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Analyze query and determine appropriate workflow"""
        
        # First, determine if this is a construction-related query
        messages = [
            {
                "role": "system",
                "content": """You are an expert at analyzing queries and determining their domain.
                First, determine if a query is construction-related.
                If it is not construction-related, assign it to the General Assistant.
                If it is construction-related, analyze which construction specialists should handle it."""
            },
            {
                "role": "user",
                "content": f"""Analyze this query: {query}

Available agents:
{json.dumps(available_agents, indent=2)}

First determine if this is a construction-related query.
Then select the most appropriate agent(s) to handle it."""
            }
        ]

        yield {
            "type": "thinking",
            "content": "🤔 Analyzing query to determine appropriate domain and assistants...",
            "agent": self.name
        }

        # Get model response
        model = self.model_manager.select_model(
            task_type="analysis",
            required_capabilities=["analysis"]
        )

        workflow = None
        async for chunk in self.model_manager.call_with_tools(
            model=model,
            messages=messages,
            stream=True
        ):
            yield {
                "type": "thinking",
                "content": f"💭 {chunk['content']}",
                "agent": self.name
            }
            
            # Look for General Assistant if query is not construction-related
            if "not construction-related" in chunk['content'].lower():
                workflow = {
                    "primary_assistant": "general_assistant",
                    "supporting_assistants": []
                }
                break
                
            # For construction queries, determine specific agents
            if "construction" in chunk['content'].lower():
                # Find most relevant construction agent
                construction_agents = [
                    agent for agent in available_agents 
                    if agent["name"] in ["Construction Coordinator", "Construction Meeting"]
                ]
                
                if construction_agents:
                    workflow = {
                        "primary_assistant": construction_agents[0]["name"],
                        "supporting_assistants": [
                            {"name": agent["name"], "role": "Support and specialized input"}
                            for agent in construction_agents[1:]
                        ]
                    }

        if workflow:
            yield {
                "type": "workflow",
                "content": {"workflow": workflow},
                "agent": self.name
            }

    async def process(self, query: str, **kwargs) -> str:
        """Process a query (required by BaseAgent)"""
        full_response = []
        async for chunk in self.analyze_query(query, kwargs.get("available_assistants", [])):
            if chunk["type"] == "workflow":
                full_response.append(json.dumps(chunk["content"], indent=2))
        return "\n".join(full_response)

    def can_handle(self, query: str) -> float:
        """Always returns 1.0 as the Manager can handle any construction query for analysis"""
        return 1.0 