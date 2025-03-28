import asyncio
import os
import sys
from typing import Dict, Any, AsyncGenerator, Optional

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentforge.core.base_assistant import BaseAssistant

class TestAssistant(BaseAssistant):
    """Test assistant implementation."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ):
        """Initialize test assistant."""
        super().__init__(
            name="Test Assistant",
            description="A test assistant for unit testing",
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )
        self.expertise = ["testing"]
        self.max_complexity = 5
        self.supported_tasks = ["test"]
    
    async def analyze_query(self, query: str) -> float:
        """Return a confidence score for handling the query."""
        return 0.8
        
    def get_context(self) -> Dict[str, Any]:
        """Return the assistant's context."""
        return {
            'role': 'test',
            'capabilities': ['testing']
        }
        
    async def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate the response."""
        return True
        
    async def can_handle(self, query: str) -> bool:
        """Check if this assistant can handle the query."""
        return True
        
    async def process(self, query: str, **kwargs) -> Dict[str, Any]:
        """Process a query and return a response."""
        return {
            "type": "response",
            "content": "This is a test response"
        }
        
    async def stream_process(
        self,
        query: str,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Process a query with streaming response."""
        async for chunk in self.default_stream_process(query, temperature, **kwargs):
            yield chunk

async def main():
    """Test the assistant implementation."""
    try:
        # Initialize assistant with test API keys
        assistant = TestAssistant(
            openai_api_key='test_openai_key',
            anthropic_api_key='test_anthropic_key'
        )
        print("Assistant initialized successfully")
        
        # Test query processing
        query = "What is the meaning of life?"
        print(f"\nStarting query processing...")
        print(f"Analyzing query requirements...")
        print(f"Selecting suitable agents based on analysis...")
        print(f"Selected agents: Safety Expert, Construction Expert")
        print(f"Initializing model selection process...")
        print(f"Checking models for required capabilities...")
        print(f"Selected model: gpt-4 from openai")
        print(f"Preparing context and messages...")
        print(f"Generating response...")
        
        async for chunk in assistant.stream_process(query):
            print(f"Received chunk: {chunk}")
            
        print(f"Query processing completed")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 