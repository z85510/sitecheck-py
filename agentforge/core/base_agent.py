from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, AsyncGenerator
from ..utils.model_manager import ModelManager
from ..utils.document_manager import DocumentManager
from ..assistants.configs.assistant_config import AssistantConfig

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(
        self,
        name: str,
        description: str,
        config_path: Optional[str] = None,
        config: Optional[AssistantConfig] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ):
        self.name = name
        self.description = description
        self.config_path = config_path
        self.config = config
        
        # Initialize managers
        self.model_manager = ModelManager(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key
        )
        
        self.document_manager = DocumentManager(
            base_path=base_path,
            openai_api_key=openai_api_key,
            collection_name=f"agentforge_{name.lower().replace(' ', '_')}"
        )
        
        # Default task types and keywords
        self.task_types = config.task_types if config else []
        self.keywords = config.keywords if config else []
        
        # Load configuration file if exists and no config object provided
        if not config and config_path:
            self._load_config()
        
    def _load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config_content = f.read()
        except FileNotFoundError:
            print(f"Warning: File {self.config_path} not found")
            self.config_content = ""
            
    @abstractmethod
    async def process(self, query: str, **kwargs) -> str:
        """Process the input query and return a response."""
        pass
    
    def update_context(self, new_context: Dict[str, Any]) -> None:
        """Update the agent's context with new information."""
        self.context.update(new_context)
    
    @abstractmethod
    def can_handle(self, query: str) -> float:
        """
        Determine if this agent can handle the given query.
        Returns a confidence score between 0 and 1.
        """
        pass
    
    async def stream_process(
        self,
        query: str,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a query and stream the response."""
        try:
            # Select appropriate model
            model = self.model_manager.select_model(
                task_type="general",
                required_capabilities=["conversation"],
                temperature=temperature
            )
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": self.get_context()
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
            
            # Stream response
            async for chunk in self.model_manager.call_with_tools(
                model=model,
                messages=messages,
                temperature=temperature,
                stream=True
            ):
                yield {
                    "type": chunk["type"],
                    "content": chunk["content"],
                    "agent": self.name
                }
                
        except Exception as e:
            yield {
                "type": "error",
                "content": f"Error in {self.name}: {str(e)}",
                "agent": self.name
            }
        
    async def get_relevant_documents(
        self,
        query: str,
        file_types: Optional[List[str]] = None,
        num_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Get relevant documents for the query"""
        try:
            docs = await self.document_manager.query_documents(
                query=query,
                assistant_name=self.name,
                file_types=file_types,
                num_results=num_results
            )
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in docs
            ]
        except Exception as e:
            print(f"Warning: Error querying documents: {str(e)}")
            return []
            
    async def process_documents(self, dir_path: str) -> Dict[str, Any]:
        """Process documents in the specified directory"""
        try:
            return await self.document_manager.process_directory(
                dir_path=dir_path,
                assistant_name=self.name
            )
        except Exception as e:
            print(f"Warning: Error processing documents: {str(e)}")
            return {
                "processed": 0,
                "unchanged": 0,
                "errors": 1,
                "error_files": [{"error": str(e)}]
            } 