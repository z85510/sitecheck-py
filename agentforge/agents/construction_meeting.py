from typing import Dict, Any, AsyncGenerator, Optional
from .specialized_agent import SpecializedAgent
from ..assistants.configs.assistant_config import ASSISTANT_CONFIGS

class ConstructionMeeting(SpecializedAgent):
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ):
        config = ASSISTANT_CONFIGS["construction_meeting"]
        super().__init__(
            name=config.name,
            description=config.description,
            config=config,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )
        
        # Add meeting-specific task types and keywords
        self.task_types.extend([
            "meeting_management",
            "action_tracking",
            "minutes_preparation",
            "follow_up_coordination",
            "decision_documentation"
        ])
        
        self.keywords.extend([
            "meeting",
            "agenda",
            "minutes",
            "action",
            "decision",
            "follow-up",
            "attendee",
            "discussion",
            "resolution",
            "schedule"
        ])
        
    async def stream_process(
        self,
        query: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process construction meeting queries with specialized context"""
        # Add meeting-specific context to the query
        enhanced_query = f"""As a Construction Meeting Assistant, analyze and respond to the following query:

{query}

Consider:
1. Meeting purpose and objectives
2. Required attendees and roles
3. Agenda structure and time allocation
4. Documentation requirements
5. Action item tracking and follow-up
6. Decision documentation needs
7. Communication protocols

Please provide a structured response that addresses these aspects as relevant to the query."""

        async for chunk in super().stream_process(enhanced_query, **kwargs):
            yield chunk
            
    def can_handle(self, query: str) -> float:
        """
        Determine confidence in handling construction meeting queries
        Returns a score between 0 and 1
        """
        query_lower = query.lower()
        
        # Check for meeting-specific keywords
        meeting_keywords = [
            "meeting", "agenda", "minutes", "notes",
            "action", "follow", "decision", "attendee",
            "discuss", "review", "update", "progress"
        ]
        
        keyword_matches = sum(1 for keyword in meeting_keywords if keyword in query_lower)
        
        # Check for construction context
        construction_context = any(word in query_lower for word in [
            "construction", "project", "site", "build",
            "contractor", "subcontractor", "team",
            "progress", "schedule", "safety"
        ])
        
        if not construction_context:
            return 0.0
            
        # Calculate confidence score
        base_score = min(keyword_matches / len(meeting_keywords), 0.8)
        context_boost = 0.2 if construction_context else 0.0
        
        return min(base_score + context_boost, 1.0) 