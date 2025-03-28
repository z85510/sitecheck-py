from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator, Optional, List
from ..utils.model_manager import ModelManager

class BaseAssistant(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        role: str,
        task_types: List[str],
        keywords: List[str],
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ):
        self.name = name
        self.description = description
        self.role = role
        self.task_types = task_types
        self.keywords = keywords
        self.base_path = base_path
        
        # Initialize model manager
        self.model_manager = ModelManager(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key
        )

    @abstractmethod
    async def analyze_query(self, query: str) -> float:
        """
        Analyze if this assistant can handle the query.
        Returns a confidence score between 0 and 1.
        """
        pass

    @abstractmethod
    async def stream_process(
        self,
        query: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process the query and stream back responses.
        """
        pass

    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        """
        Return the assistant's context including role, capabilities, etc.
        """
        pass

    @abstractmethod
    async def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate if a response meets the assistant's quality standards.
        """
        pass

    async def _generate_response(
        self,
        query: str,
        temperature: float = 0.7,
        preferred_model: Optional[str] = None,
        model_type: Optional[str] = None,
        model_category: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a response using the model manager.
        This is a helper method that can be used by implementing classes.
        """
        # Select appropriate model
        model = self.model_manager.select_model(
            task_type=self.task_types[0],  # Use first task type as primary
            required_capabilities=["conversation"],  # Basic capability
            temperature=temperature,
            preferred_model=preferred_model,
            model_type=model_type,
            model_category=model_category
        )
        
        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": f"{self.role}\n\nTask Types: {', '.join(self.task_types)}"
            },
            {
                "role": "user",
                "content": query
            }
        ]
        
        # Generate response
        async for chunk in self.model_manager.call_with_tools(
            model=model,
            messages=messages,
            stream=True,
            temperature=temperature
        ):
            yield chunk 