from typing import Dict, Any, AsyncGenerator, Optional, List
from ..core.base_assistant import BaseAssistant

class GeneralAssistant(BaseAssistant):
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ):
        super().__init__(
            name="General Assistant",
            description="A general-purpose assistant that handles non-specialized queries",
            role="""You are a helpful general-purpose assistant that handles queries not requiring specialized domain knowledge.
            You provide clear, concise, and relevant responses while recognizing when to defer to specialists.""",
            task_types=["general_assistance", "information", "conversation"],
            keywords=["help", "information", "question", "general"],
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )

    async def analyze_query(self, query: str) -> float:
        """Analyze if this assistant should handle the general query"""
        # Check if query contains specialized keywords that other assistants should handle
        specialized_indicators = [
            "safety", "construction", "audit", "compliance",
            "incident", "emergency", "hazard", "risk"
        ]
        
        # If query contains specialized keywords, return low confidence
        if any(indicator.lower() in query.lower() for indicator in specialized_indicators):
            return 0.3
        
        # Otherwise, return medium confidence as the fallback handler
        return 0.5

    async def stream_process(
        self,
        query: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process general queries with a friendly, helpful approach"""
        
        # 1. Initial acknowledgment
        yield {
            "type": "thinking",
            "content": "🤔 Analyzing your question...",
            "agent": self.name
        }

        # 2. Generate and stream the response
        async for chunk in self._generate_response(query, **kwargs):
            yield chunk

    def get_context(self) -> Dict[str, Any]:
        """Return the general assistant's context"""
        return {
            "name": self.name,
            "description": self.description,
            "role": self.role,
            "task_types": self.task_types,
            "keywords": self.keywords,
            "capabilities": [
                "General information queries",
                "Basic task assistance",
                "Non-specialized help",
                "Conversation and clarification"
            ]
        }

    async def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate if the response meets general assistance standards"""
        required_elements = [
            "content",  # Must have actual content
            "is_complete",  # Must indicate if the response is complete
            "needs_specialist"  # Must indicate if a specialist should be consulted
        ]
        
        return all(element in response for element in required_elements)

    async def _generate_response(
        self,
        query: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a helpful general response"""
        # Implementation would use the model manager to generate responses
        # This is a placeholder for the actual implementation
        yield {
            "type": "response",
            "content": "Let me help you with that...",
            "agent": self.name,
            "is_complete": True,
            "needs_specialist": False
        } 