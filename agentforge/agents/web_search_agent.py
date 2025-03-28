"""
Web Search Agent for handling internet-based queries.
"""

import logging
from typing import Dict, Any, AsyncGenerator, Optional
import json
from ..core.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class WebSearchAgent(BaseAgent):
    """Specialized agent for performing web searches and processing internet data."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge",
        name: str = "Web Search Specialist",
        description: str = "Expert in retrieving and analyzing information from the internet"
    ):
        super().__init__(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path,
            name=name,
            description=description
        )

    async def can_handle(self, query: str) -> bool:
        """Check if this agent should handle the query."""
        return True  # This agent can handle any web search query

    async def process(self, query: str, **kwargs) -> str:
        """Process a web search query and return compiled results."""
        response_chunks = []
        async for chunk in self.stream_process(query, **kwargs):
            if chunk["type"] == "content":
                response_chunks.append(chunk["content"])
        return "".join(response_chunks)

    async def search_and_analyze(self, query: str) -> str:
        """Perform web search and analyze results."""
        try:
            search_results = []
            
            # Define web search tool with proper function configuration
            web_search_tool = {
                "type": "web_search",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for real-time information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
            
            # Collect all chunks from the web search
            async for chunk in self.model_manager.call_with_tools(
                model="gpt-4",
                provider="openai",
                messages=[{
                    "role": "user", 
                    "content": f"Search the web for: {query}"
                }],
                tools=[web_search_tool],
                stream=True
            ):
                if chunk.get("type") == "response":
                    search_results.append(chunk.get("content", ""))
            
            raw_results = "".join(search_results)
            
            # Analyze and summarize the results
            analysis_prompt = (
                f'Web search results for query: "{query}"\n\n'
                f'Raw Results:\n{raw_results}\n\n'
                'Please provide a clear, well-organized summary that:\n'
                '1. Extracts key information\n'
                '2. Organizes facts logically\n'
                '3. Highlights important findings\n'
                '4. Maintains accuracy\n'
                '5. Cites sources when possible'
            )

            analysis_results = []
            async for chunk in self.model_manager.call_with_tools(
                model="gpt-4",
                provider="openai",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a web research specialist. Analyze and summarize web search results accurately and concisely."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                stream=True
            ):
                if chunk.get("type") == "response":
                    analysis_results.append(chunk.get("content", ""))
            
            return "".join(analysis_results)
            
        except Exception as e:
            logger.error(f"Error in search_and_analyze: {str(e)}")
            return f"Error performing web search and analysis: {str(e)}"

    async def stream_process(
        self,
        query: str,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process the query with real-time updates."""
        try:
            yield {
                "type": "thinking",
                "message": "🌐 Initiating web search..."
            }

            # Define web search tool with proper function configuration
            web_search_tool = {
                "type": "web_search",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for real-time information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }

            # Optimize search query
            search_prompt = (
                f'Original query: "{query}"\n'
                'Create 1-2 focused search queries that will help find relevant information.\n'
                'Return only the search queries, one per line.'
            )
            
            search_queries = []
            async for chunk in self.model_manager.call_with_tools(
                model="gpt-4",
                provider="openai",
                messages=[{"role": "user", "content": search_prompt}],
                tools=[web_search_tool],
                stream=True
            ):
                if chunk.get("type") == "response":
                    search_queries.extend(
                        [q.strip() for q in chunk.get("content", "").split("\n") if q.strip()]
                    )

            # Perform searches
            all_results = []
            for search_query in search_queries[:2]:  # Limit to 2 queries
                yield {
                    "type": "thinking",
                    "message": f"🔍 Searching for: {search_query}"
                }
                
                result = await self.search_and_analyze(search_query)
                all_results.append(result)

            yield {
                "type": "thinking",
                "message": "✨ Synthesizing search results..."
            }

            # Synthesize results
            synthesis_prompt = (
                f'Original query: "{query}"\n\n'
                f'Search Results:\n{chr(10).join(all_results)}\n\n'
                'Provide a comprehensive response that:\n'
                '1. Directly answers the original query\n'
                '2. Integrates information from all search results\n'
                '3. Maintains accuracy and cites sources when possible\n'
                '4. Organizes information logically\n'
                '5. Highlights key findings and insights'
            )

            async for chunk in self.model_manager.call_with_tools(
                model="gpt-4",
                provider="openai",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are {self.name}, {self.description}."
                    },
                    {
                        "role": "user",
                        "content": synthesis_prompt
                    }
                ],
                temperature=temperature,
                stream=True
            ):
                if chunk.get("type") == "response":
                    yield {
                        "type": "content",
                        "content": chunk.get("content", "")
                    }

            yield {
                "type": "thinking",
                "message": "✅ Web search complete!"
            }

        except Exception as e:
            logger.error(f"Error in stream_process: {str(e)}")
            yield {"type": "error", "error": str(e)} 