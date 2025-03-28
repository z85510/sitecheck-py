from typing import List
from ..core.base_agent import BaseAgent
from .manager_assistant import ManagerAssistant

def get_all_agents(
    openai_api_key: str = None,
    anthropic_api_key: str = None,
    base_path: str = "agentforge"
) -> List[BaseAgent]:
    """Get all available agents initialized with the provided API keys."""
    return [
        ManagerAssistant(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )
    ]

__all__ = [
    'get_all_agents',
    'ManagerAssistant'
] 