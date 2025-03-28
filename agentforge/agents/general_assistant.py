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
            name="general_assistant",
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
        async for chunk in self._generate_response(
            query=query,
            temperature=kwargs.get("temperature", 0.7),
            preferred_model=kwargs.get("preferred_model"),
            model_type=kwargs.get("model_type"),
            model_category=kwargs.get("model_category")
        ):
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
        try:
            # Select appropriate model
            model = self.model_manager.select_model(
                task_type="conversation",
                required_capabilities=["conversation"],
                temperature=kwargs.get("temperature", 0.7),
                preferred_model=kwargs.get("preferred_model"),
                model_type=kwargs.get("model_type"),
                model_category=kwargs.get("model_category")
            )
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": f"""You are a helpful general-purpose AI assistant named {self.name}.
                    {self.role}
                    
                    Task Types: {', '.join(self.task_types)}
                    
                    For general queries and greetings:
                    1. Provide warm, welcoming responses while maintaining professionalism
                    2. Keep responses clear, concise, and relevant
                    3. If a query requires specialized knowledge, indicate that in your response
                    4. ALWAYS provide a meaningful response, even for simple greetings
                    
                    Always respond in a friendly and helpful manner.
                    Never return an empty response."""
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
            
            # Generate response
            response_started = False
            async for chunk in self.model_manager.call_with_tools(
                model=model,
                messages=messages,
                stream=True,
                temperature=kwargs.get("temperature", 0.7)
            ):
                if chunk["type"] == "response":
                    if chunk.get("content"):  # Only yield non-empty content
                        response_started = True
                        yield {
                            "type": "response",
                            "content": chunk["content"],
                            "agent": self.name,
                            "is_complete": True,
                            "needs_specialist": False
                        }
                else:
                    yield chunk
                    
            # If no response was generated, provide a default response
            if not response_started:
                yield {
                    "type": "response",
                    "content": "I understand your message and I'm here to help. Could you please provide more details about what you'd like assistance with?",
                    "agent": self.name,
                    "is_complete": True,
                    "needs_specialist": False
                }
                
        except Exception as e:
            # Log the error and provide a friendly error response
            print(f"Error generating response: {str(e)}")
            yield {
                "type": "response",
                "content": "I apologize, but I encountered an issue while processing your request. Could you please try rephrasing your question?",
                "agent": self.name,
                "is_complete": True,
                "needs_specialist": False
            } 