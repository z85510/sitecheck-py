from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator, Optional, List
from ..utils.model_manager import ModelManager
from .base_agent import BaseAgent
import logging
import json
import traceback

logger = logging.getLogger(__name__)

class BaseAssistant(BaseAgent):
    """Base class for all AI assistants."""
    
    def __init__(
        self,
        name: str,
        description: str,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ):
        """Initialize the base assistant.
        
        Args:
            name: Assistant name
            description: Assistant description
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
            base_path: Base path for vector storage
        """
        # Initialize BaseAgent
        super().__init__(
            name=name,
            description=description,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )
        
        # Set basic properties
        self.expertise = []
        self.max_complexity = 5
        self.supported_tasks = []
        self.base_path = base_path
        
        # Initialize model manager with API keys
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
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a query and stream the response."""
        try:
            # Get context for the query
            context = await self.get_context(query)
            
            # Validate query and context
            if not self.validate_response(query):
                yield {
                    "type": "error",
                    "content": "Invalid query format or content"
                }
                return

            # Check if we need clarification
            clarification_needed = await self._check_clarification_needed(query, context)
            if clarification_needed:
                yield {
                    "type": "clarification_needed",
                    "query": clarification_needed
                }
                return

            # Prepare messages for the model
            messages = [
                {"role": "system", "content": self.description},
                {"role": "user", "content": f"Context:\n{json.dumps(context, indent=2)}\n\nQuery: {query}"}
            ]

            # Stream response from model
            async for response in self.model_manager.call_with_tools(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
                **kwargs
            ):
                yield response

        except Exception as e:
            logger.error(f"Error in stream_process: {str(e)}")
            yield {
                "type": "error",
                "content": f"Error processing query: {str(e)}"
            }

    async def _check_clarification_needed(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Check if clarification is needed for the query."""
        # Prepare messages to check for clarification
        messages = [
            {"role": "system", "content": f"""You are {self.name}. Your task is to determine if you need clarification 
            to properly answer the query. If you need clarification, explain what specific information you need.
            If you don't need clarification, respond with 'No clarification needed.'"""},
            {"role": "user", "content": f"Context:\n{json.dumps(context, indent=2)}\n\nQuery: {query}"}
        ]

        clarification_response = ""
        async for response in self.model_manager.call_with_tools(
            model=self.model,
            messages=messages,
            temperature=0.3,  # Lower temperature for more focused clarification check
            stream=False
        ):
            if response["type"] == "response":
                clarification_response += response["content"]

        if "no clarification needed" in clarification_response.lower():
            return None

        return clarification_response.strip()

    async def default_stream_process(
        self,
        query: str,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Default implementation for streaming response processing.
        
        Args:
            query: The user's query
            temperature: Response randomness (0-1)
            **kwargs: Additional parameters
            
        Yields:
            dict: Response chunks with type and content
        """
        # First yield thinking message
        yield {
            "type": "thinking",
            "content": f"Let me think about that..."
        }
        
        try:
            # Generate response
            async for chunk in self._generate_response(
                query=query,
                temperature=temperature,
                **kwargs
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in stream_process: {str(e)}")
            yield {
                "type": "error",
                "content": f"I apologize, but I encountered an error while processing your request: {str(e)}"
            }

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
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a response to the given query."""
        try:
            yield {
                "type": "workflow",
                "step": "start",
                "content": f"🤖 Starting response generation with {self.name}..."
            }

            # Select appropriate model
            yield {
                "type": "workflow",
                "step": "model_selection",
                "content": "🔄 Selecting appropriate AI model..."
            }

            try:
                model, provider = await self.model_manager.select_model(
                    query=query,
                    preferred_model=self.preferred_model,
                    required_capabilities=self.required_capabilities,
                    temperature=temperature
                )
                
                yield {
                    "type": "workflow",
                    "step": "model_selected",
                    "content": f"✅ Selected model: {model} from {provider}"
                }
            except Exception as e:
                yield {
                    "type": "error",
                    "content": f"❌ Error selecting model: {str(e)}"
                }
                raise

            # Prepare context and generate response
            yield {
                "type": "workflow",
                "step": "context",
                "content": "📝 Preparing context and generating response..."
            }

            context = self._prepare_context(query, **kwargs)
            
            async for chunk in self.model_manager.call_with_tools(
                model=model,
                provider=provider,
                messages=context,
                temperature=temperature,
                **kwargs
            ):
                if isinstance(chunk, dict):
                    yield chunk
                else:
                    yield {
                        "type": "response",
                        "content": chunk,
                        "agent": self.name
                    }

            yield {
                "type": "workflow",
                "step": "complete",
                "content": "✅ Response generation completed"
            }

        except Exception as e:
            yield {
                "type": "error",
                "content": f"❌ Error generating response: {str(e)}",
                "agent": self.name
            }
            logger.error(f"Error generating response: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _prepare_context(self, query: str, **kwargs) -> List[Dict[str, str]]:
        """Prepare the context for the model."""
        return [
            {
                "role": "system",
                "content": f"""You are {self.name}. {self.description}
Your areas of expertise are: {', '.join(self.expertise)}
Focus on providing accurate and helpful responses within your expertise."""
            },
            {"role": "user", "content": query}
        ] 