from typing import Any, Dict, Optional, List, AsyncGenerator
import os
import json
from ..core.base_agent import BaseAgent
from ..assistants.configs.assistant_config import AssistantConfig

class SpecializedAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        description: str,
        config: AssistantConfig,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ):
        super().__init__(
            name=name,
            description=description,
            config=config,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )
        self.instructions = config.instructions
        self.files = self._load_files()
        
    def _load_files(self) -> Dict[str, str]:
        """Load all associated files for this assistant."""
        files_content = {}
        base_path = os.path.join(os.path.dirname(__file__), "../assistants/files")
        
        for filename in self.config.files:
            try:
                with open(os.path.join(base_path, filename), 'r') as f:
                    files_content[filename] = f.read()
            except FileNotFoundError:
                print(f"Warning: File {filename} not found")
        
        return files_content
    
    def _prepare_system_message(self) -> str:
        """Prepare the system message including instructions and relevant file contents."""
        system_message = f"{self.instructions}\n\nRelevant files and guidelines:\n"
        for filename, content in self.files.items():
            system_message += f"\n{filename}:\n{content}\n"
        return system_message
    
    async def stream_thinking(self, thought: str):
        """Stream thinking process"""
        return {
            "type": "thinking",
            "content": thought,
            "agent": self.name
        }

    async def stream_process(
        self,
        query: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a query with relevant document context"""
        try:
            # Get relevant documents
            docs = await self.get_relevant_documents(query)
            
            # Prepare context from documents
            doc_context = ""
            if docs:
                doc_context = "\n\nRelevant context from documents:\n"
                for doc in docs:
                    doc_context += f"\nFrom {doc['metadata']['source']}:\n{doc['content']}\n"
                    
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": f"""You are a specialized assistant for {self.name}.
                    
{self._prepare_system_message()}

Your task is to help with the following query, using any relevant context provided."""
                },
                {
                    "role": "user",
                    "content": f"{query}\n{doc_context}"
                }
            ]
            
            # Select appropriate model
            model = self.model_manager.select_model(
                task_type="document_analysis" if docs else "general",
                required_capabilities=["tool_calling"],
                temperature=kwargs.get("temperature", 0.7)
            )
            
            # Stream response
            yield json.dumps({
                "type": "thinking",
                "content": f"Analyzing query with {model}...",
                "agent": self.name
            })
            
            # Make API call
            async for chunk in self.model_manager.call_with_tools(
                model=model,
                messages=messages,
                tools=[],  # Add tools if needed
                temperature=kwargs.get("temperature", 0.7),
                stream=True
            ):
                yield json.dumps({
                    "type": "response",
                    "content": chunk["content"],
                    "agent": self.name
                })
            
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "content": f"Error processing query: {str(e)}",
                "agent": self.name
            })
            
    def can_handle(self, query: str) -> float:
        """
        Calculate confidence score based on task types and keywords
        """
        query_lower = query.lower()
        
        # Check task types
        task_matches = sum(1 for task in self.task_types if task.lower() in query_lower)
        
        # Check keywords
        keyword_matches = sum(1 for keyword in self.keywords if keyword.lower() in query_lower)
        
        # Calculate score
        if not (self.task_types or self.keywords):
            return 0.0
            
        total_items = len(self.task_types) + len(self.keywords)
        total_matches = task_matches + keyword_matches
        
        return min(total_matches / total_items if total_items > 0 else 0.0, 1.0)
        
    async def process(self, query: str, **kwargs) -> str:
        """Process a query and return a response"""
        full_response = []
        async for chunk in self.stream_process(query, **kwargs):
            if chunk["type"] == "response":
                full_response.append(chunk["content"])
        return "".join(full_response) 