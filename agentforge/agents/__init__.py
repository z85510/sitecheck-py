from typing import List
from ..core.base_agent import BaseAgent
from .safety_assistant import SafetyAssistant
from .construction_meeting import ConstructionMeeting
from .general_assistant import GeneralAssistant

def get_all_agents(
    openai_api_key: str = None,
    anthropic_api_key: str = None,
    base_path: str = "agentforge"
) -> List[BaseAgent]:
    """Get all available agents initialized with the provided API keys."""
    return [
        SafetyAssistant(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        ),
        ConstructionMeeting(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        ),
        GeneralAssistant(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )
    ]

__all__ = [
    'SafetyAssistant',
    'ConstructionMeeting',
    'GeneralAssistant',
    'get_all_agents'
] 