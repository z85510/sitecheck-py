"""
SERP (Search Engine Results Page) Agent for advanced web search and analysis using SerpApi.
"""

import logging
import asyncio
from typing import Dict, Any, AsyncGenerator, Optional, List, Tuple
import json
import aiohttp
import os
from urllib.parse import quote_plus
from ..core.base_agent import BaseAgent
import ssl

logger = logging.getLogger(__name__)

class SerpAgent(BaseAgent):
    """Advanced SERP agent for parallel web searches and comprehensive analysis."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge",
        name: str = "SERP Specialist",
        description: str = "Expert in advanced web search, analysis, and information synthesis",
        serpapi_key: Optional[str] = None
    ):
        super().__init__(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path,
            name=name,
            description=description
        )
        # Get SERP API key from environment variable or passed parameter
        self.serpapi_key = serpapi_key or os.getenv('SERP_API_KEY')
        if not self.serpapi_key:
            raise ValueError("SERP_API_KEY not found in environment variables and not provided to constructor")
        
        # Search categories for different types of content
        self.search_categories = {
            "recent": {
                "suffix": "latest news updates current information",
                "weight": 1.0,
                "time_range": "d" # last day
            },
            "official": {
                "suffix": "official website documentation",
                "weight": 1.2,
                "time_range": "m" # last month
            },
            "technical": {
                "suffix": "technical details specifications features",
                "weight": 0.8,
                "time_range": "m"
            },
            "discussion": {
                "suffix": "reddit forum discussion community",
                "weight": 0.6,
                "time_range": "m"
            }
        }

    async def generate_search_queries(self, query: str) -> List[Tuple[str, float]]:
        """Generate optimized search queries for different search categories.
        
        Args:
            query: The original user query
            
        Returns:
            List of tuples containing (optimized_query, weight)
        """
        # Remove any search command prefixes
        clean_query = query.replace("/web", "").replace("/search", "").strip()
        
        # Generate queries for each category
        queries = []
        
        # Get query intent using LLM
        intent_prompt = f"""Analyze this search query and determine its primary intent:
Query: "{clean_query}"

Respond with one of these categories:
- RECENT: For current events, latest updates, or time-sensitive information
- OFFICIAL: For official documentation, specifications, or authoritative sources
- TECHNICAL: For technical details, how-tos, or specifications
- DISCUSSION: For community insights, experiences, or discussions

Category:"""

        intent_response = ""
        async for chunk in self.model_manager.call_with_tools(
            model="gpt-3.5-turbo",
            provider="openai",
            messages=[
                {"role": "system", "content": "You are a search query analyzer. Respond only with the category name."},
                {"role": "user", "content": intent_prompt}
            ],
            stream=True
        ):
            if chunk.get("type") == "response":
                intent_response += chunk.get("content", "")
        
        # Normalize the intent response
        primary_intent = intent_response.strip().lower()
        
        # Add queries based on intent, prioritizing the primary intent category
        for category, info in self.search_categories.items():
            # Adjust weight based on whether this category matches the primary intent
            weight = info["weight"]
            if category.lower() in primary_intent:
                weight *= 1.5  # Boost weight for primary intent category
            
            # Create optimized query for this category
            optimized_query = f"{clean_query} {info['suffix']}"
            queries.append((optimized_query, weight))
        
        return queries

    async def can_handle(self, query: str) -> bool:
        """Check if this agent can handle the query.
        
        The SERP agent should only handle queries when:
        1. Explicitly requested with /web command
        2. Other agents' responses are marked as incomplete
        3. Manager specifically requests additional web information
        """
        # Check if this is an explicit web search request
        if "/web" in query.lower():
            return True
            
        # Check for incomplete information markers
        incomplete_markers = [
            "insufficient information",
            "need more details",
            "additional information required",
            "information not found",
            "no local data",
            "requires web search",
            "check online",
            "verify online",
            "look up online",
            "search web for"
        ]
        
        # Only handle if query explicitly indicates need for web search
        return any(marker.lower() in query.lower() for marker in incomplete_markers)

    async def process(self, query: str, **kwargs) -> str:
        """Process a query and return a response.
        
        This is a non-streaming version that collects all chunks into a single response.
        For streaming responses, use stream_process instead.
        """
        response_chunks = []
        async for chunk in self.stream_process(query, **kwargs):
            if chunk["type"] == "content":
                response_chunks.append(chunk["content"])
        return "".join(response_chunks)

    async def serpapi_search(self, query: str) -> Dict[str, Any]:
        """Perform a search using SerpApi."""
        try:
            # Encode query for URL
            encoded_query = quote_plus(query)
            
            # Build URL with parameters
            url = f"https://serpapi.com/search.json?engine=google&q={encoded_query}&api_key={self.serpapi_key}"
            
            # Configure SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE  # Only for development/testing
            
            # Configure client session with SSL context
            conn = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=conn) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract organic results
                        results = []
                        if "organic_results" in data:
                            for result in data["organic_results"][:5]:  # Limit to top 5 results
                                snippet = {
                                    "title": result.get("title", ""),
                                    "link": result.get("link", ""),
                                    "snippet": result.get("snippet", ""),
                                    "date": result.get("date", "")
                                }
                                results.append(snippet)
                        
                        # Extract news results if available
                        if "news_results" in data:
                            for result in data["news_results"][:3]:  # Limit to top 3 news
                                snippet = {
                                    "title": result.get("title", ""),
                                    "link": result.get("link", ""),
                                    "snippet": result.get("snippet", ""),
                                    "date": result.get("date", ""),
                                    "source": result.get("source", "")
                                }
                                results.append(snippet)
                        
                        return {
                            "query": query,
                            "results": results
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"SerpApi error: {error_text}")
                        
        except Exception as e:
            logger.error(f"Error in serpapi_search: {str(e)}")
            return {
                "query": query,
                "results": [],
                "error": str(e)
            }

    async def parallel_search(self, queries: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
        """Perform parallel web searches for multiple queries."""
        try:
            async def search_single_query(query: str, weight: float) -> Dict[str, Any]:
                """Perform a single web search."""
                # Determine time range based on query
                time_range = None
                for category, info in self.search_categories.items():
                    if info["suffix"] in query.lower():
                        time_range = info["time_range"]
                        break
                
                # Perform search
                search_result = await self.serpapi_search(query)
                
                return {
                    "query": query,
                    "weight": weight,
                    "content": json.dumps(search_result["results"], indent=2)
                }
            
            # Run searches in parallel
            tasks = [search_single_query(query, weight) for query, weight in queries]
            results = await asyncio.gather(*tasks)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in parallel search: {str(e)}")
            return []

    async def analyze_results(self, results: List[Dict[str, Any]], original_query: str) -> str:
        """Analyze and synthesize search results with weighted importance."""
        try:
            # Prepare results for analysis
            weighted_results = []
            for result in results:
                if result["content"]:
                    weighted_results.append({
                        "content": result["content"],
                        "importance": result["weight"]
                    })
            
            if not weighted_results:
                return "No search results found."
            
            # Create analysis prompt
            analysis_prompt = (
                f'Original Query: "{original_query}"\n\n'
                'Search Results (with importance weights):\n\n'
            )
            
            for idx, result in enumerate(weighted_results, 1):
                analysis_prompt += (
                    f'[Result {idx} (importance: {result["importance"]})]\n'
                    f'{result["content"]}\n\n'
                )
            
            analysis_prompt += (
                'Provide a comprehensive analysis that:\n'
                '1. Prioritizes information based on importance weights\n'
                '2. Cross-references facts across sources\n'
                '3. Highlights consensus and contradictions\n'
                '4. Cites sources and their credibility\n'
                '5. Provides timestamp/date context for time-sensitive information\n'
                '6. Organizes information by relevance and reliability'
            )
            
            # Analyze results
            analysis_results = []
            async for chunk in self.model_manager.call_with_tools(
                model="gpt-4",
                provider="openai",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert research analyst. Synthesize information with attention to source credibility, timeliness, and cross-validation."
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
            logger.error(f"Error analyzing results: {str(e)}")
            return f"Error analyzing search results: {str(e)}"

    async def stream_process(
        self,
        query: str,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process the query with up to two search attempts."""
        try:
            # Initial analysis stage
            yield {
                "type": "status",
                "content": "🔄 Initializing web search process...",
                "details": {}
            }
            
            # Clean query and check if it's a direct web search
            clean_query = query.replace("/web", "").replace("/search", "").strip()
            is_direct_web_search = "/web" in query.lower()
            
            if not is_direct_web_search:
                yield {
                    "type": "analyzing",
                    "content": "🔍 Analyzing need for additional web information...",
                    "details": {}
                }
            
            # Search stage
            yield {
                "type": "searching",
                "content": f"🌐 Searching web for: {clean_query}",
                "details": {}
            }
            
            # First search attempt
            search_results = await self.serpapi_search(clean_query)
            
            # Check if we need a second attempt
            if not search_results["results"]:
                yield {
                    "type": "analyzing",
                    "content": "🤔 No results found, refining search strategy...",
                    "details": {}
                }
                
                yield {
                    "type": "searching",
                    "content": "🔄 Performing refined search...",
                    "details": {}
                }
                
                # Add some general terms for second attempt
                refined_query = f"{clean_query} information details"
                search_results = await self.serpapi_search(refined_query)
            
            if search_results["results"]:
                # Processing stage
                yield {
                    "type": "processing",
                    "content": "📊 Processing search results...",
                    "details": {}
                }
                
                # Format results for analysis
                analysis_prompt = (
                    f'Query: "{clean_query}"\n\n'
                    'Search Results:\n\n'
                    f'{json.dumps(search_results["results"], indent=2)}\n\n'
                    'Create a comprehensive response that:\n'
                    '1. Directly answers the query\n'
                    '2. Provides context and supporting details\n'
                    '3. Includes relevant timestamps/dates\n'
                    '4. Notes source credibility\n'
                    '5. Highlights confidence levels in the information\n'
                    '6. Clearly indicates this information is from web sources'
                )
                
                # Analysis stage
                yield {
                    "type": "analyzing",
                    "content": "🧠 Synthesizing information from web sources...",
                    "details": {}
                }
                
                # Call LLM for analysis
                yield {
                    "type": "calling_llm",
                    "content": "🤖 Generating comprehensive response...",
                    "details": {}
                }
                
                async for chunk in self.model_manager.call_with_tools(
                    model="gpt-4",
                    provider="openai",
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are {self.name}, {self.description}. Clearly indicate when information comes from web sources."
                        },
                        {
                            "role": "user",
                            "content": analysis_prompt
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
                
                # Completion stage
                yield {
                    "type": "complete",
                    "content": "✅ Web search and analysis complete",
                    "details": {}
                }
            else:
                yield {
                    "type": "error",
                    "error": "No relevant results found after search refinement."
                }
            
        except Exception as e:
            logger.error(f"Error in stream_process: {str(e)}")
            yield {"type": "error", "error": str(e)} 