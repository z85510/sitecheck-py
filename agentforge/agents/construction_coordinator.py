from typing import Dict, Any, AsyncGenerator, Optional
from .specialized_agent import SpecializedAgent
from ..assistants.configs.assistant_config import ASSISTANT_CONFIGS

class ConstructionCoordinator(SpecializedAgent):
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ):
        config = ASSISTANT_CONFIGS["construction_coordinator"]
        super().__init__(
            name=config.name,
            description=config.description,
            config=config,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )
        
        # Add construction-specific task types and keywords
        self.task_types.extend([
            "project_coordination",
            "document_management",
            "quality_control",
            "schedule_management",
            "stakeholder_communication"
        ])
        
        self.keywords.extend([
            "construction",
            "project",
            "schedule",
            "quality",
            "coordination",
            "document",
            "stakeholder",
            "contractor",
            "inspection",
            "permit"
        ])
        
    async def stream_process(
        self,
        query: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process construction coordination queries with specialized context"""
        # Add construction-specific context to the query
        enhanced_query = f"""As a Construction Project Coordinator, analyze and respond to the following query:

{query}

Consider:
1. Project timeline and schedule impacts
2. Resource allocation and availability
3. Quality control requirements
4. Documentation and compliance needs
5. Stakeholder communication requirements
6. Risk assessment and mitigation strategies

Please provide a structured response that addresses these aspects as relevant to the query."""

        async for chunk in super().stream_process(enhanced_query, **kwargs):
            yield chunk
            
    def can_handle(self, query: str) -> float:
        """
        Determine confidence in handling construction coordination queries
        Returns a score between 0 and 1
        """
        query_lower = query.lower()
        
        # Check for coordination-specific keywords
        coordination_keywords = [
            "coordinate", "manage", "oversee", "plan",
            "schedule", "timeline", "resource", "budget",
            "quality", "document", "report", "stakeholder"
        ]
        
        keyword_matches = sum(1 for keyword in coordination_keywords if keyword in query_lower)
        
        # Check for construction context
        construction_context = any(word in query_lower for word in [
            "construction", "project", "site", "build",
            "contractor", "subcontractor", "permit",
            "inspection", "drawing", "specification"
        ])
        
        if not construction_context:
            return 0.0
            
        # Calculate confidence score
        base_score = min(keyword_matches / len(coordination_keywords), 0.8)
        context_boost = 0.2 if construction_context else 0.0
        
        return min(base_score + context_boost, 1.0) 