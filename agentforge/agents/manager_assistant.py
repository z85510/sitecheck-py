"""
Manager Assistant class for coordinating multiple AI assistants.
"""

import logging
from typing import Dict, Any, AsyncGenerator, List, Optional
import json
from ..core.base_agent import BaseAgent
from ..assistants.configs.assistant_configs import get_all_assistants, get_assistant_config
from ..assistants.configs.manager_config import (
    MANAGER_IDENTITY,
    INFO_STACK,
    TEAM_ROSTER,
    WORKFLOW_STEPS,
    QUALITY_STANDARDS,
    COMMUNICATION_STANDARDS,
    RESPONSE_TEMPLATES
)

logger = logging.getLogger(__name__)

class ManagerAssistant(BaseAgent):
    """Manager Assistant that coordinates other assistants based on query requirements."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge",
        name: str = MANAGER_IDENTITY["name"],
        description: str = MANAGER_IDENTITY["description"]
    ):
        super().__init__(
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path,
            name=name,
            description=description
        )
        self.available_assistants = get_all_assistants()
        self.workflow_steps = WORKFLOW_STEPS
        self.quality_standards = QUALITY_STANDARDS
        self.communication_standards = COMMUNICATION_STANDARDS
        self.response_templates = RESPONSE_TEMPLATES
        self.team_roster = TEAM_ROSTER

    async def can_handle(self, query: str) -> bool:
        """Check if this assistant can handle the query.
        
        As a manager, it can handle all queries by either processing them directly
        or delegating to other assistants.
        """
        return True

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

    async def analyze_requirements(self, query: str) -> Dict[str, Any]:
        """Analyze what tools and assistants are needed for the query."""
        # Check for explicit web search request
        explicit_web_search = any(trigger in query.lower() for trigger in [
            "/web",
            "/search",
            "search the web",
            "look up online",
            "check online",
            "find on the internet"
        ])
        
        analysis_prompt = f"""
        Analyze this query: "{query}"
        
        Determine requirements (respond in JSON):
        {{
            "needs_web_search": boolean,  // Only true if explicitly requested or absolutely necessary
            "needs_specialists": boolean,  // Does this need specialist knowledge?
            "primary_expertise_needed": "string",  // Main expertise area needed
            "secondary_expertise_needed": ["string"],  // Other expertise areas
            "required_tools": ["string"],  // e.g. ["web_search", "file_read", "code_search"]
            "search_queries": ["string"],  // Specific search queries if web search needed
            "confidence_without_web": float  // 0-1 score of confidence in answering without web search
        }}
        """
        
        response = await self.llm_call(
            analysis_prompt,
            temperature=0.3,
            max_tokens=200
        )
        
        try:
            analysis = json.loads(response)
            # Override web search based on explicit request
            analysis["needs_web_search"] = explicit_web_search or (
                analysis.get("confidence_without_web", 1.0) < 0.6 and
                analysis.get("needs_web_search", False)
            )
            return analysis
        except json.JSONDecodeError:
            return {
                "needs_web_search": explicit_web_search,
                "needs_specialists": False,
                "primary_expertise_needed": None,
                "secondary_expertise_needed": [],
                "required_tools": [],
                "search_queries": [query],
                "confidence_without_web": 1.0
            }

    async def analyze_query(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Analyze the query using AI to determine requirements."""
        yield {
            "type": "thinking",
            "message": "Analyzing query to understand requirements...",
            "details": {"query": query}
        }

        # Use AI to analyze the query
        analysis_prompt = f"""
        Analyze this query: "{query}"
        
        Follow these analysis steps:
        {json.dumps(self.workflow_steps['request_analysis']['actions'], indent=2)}
        
        Consider these quality standards:
        {json.dumps(self.quality_standards, indent=2)}
        
        Format the response as a JSON object with:
        1. Complexity level (simple/complex)
        2. Required areas of expertise
        3. Required capabilities
        4. Whether it needs multiple assistants
        5. Key topics or themes
        6. Information sufficiency assessment
        7. Appropriate specialists from: {list(self.team_roster.keys())}
        """
        
        analysis_response = await self.llm_call(
            analysis_prompt,
            temperature=0.3,
            max_tokens=1000
        )
        
        try:
            analysis = json.loads(analysis_response)
            # Add workflow metadata
            analysis["workflow_step"] = "request_analysis"
            analysis["next_step"] = (
                "knowhow_check" if analysis.get("is_clear", True)
                else "clarification_needed"
            )
        except json.JSONDecodeError:
            analysis = {
                "complexity": "complex" if len(query.split()) > 10 else "simple",
                "required_expertise": [],
                "required_capabilities": [],
                "needs_multiple_assistants": False,
                "key_topics": [],
                "is_clear": True,
                "workflow_step": "request_analysis",
                "next_step": "knowhow_check"
            }
        
        yield {
            "type": "analysis_complete",
            "message": "Analysis complete",
            "details": analysis
        }

    async def get_suitable_assistants(self, analysis: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Find suitable assistants based on AI analysis."""
        yield {
            "type": "thinking",
            "message": "Identifying suitable assistants based on requirements...",
            "details": {"requirements": analysis}
        }

        suitable_assistants = []
        for assistant_id, assistant_config in self.team_roster.items():
            if assistant_id == "manager":
                continue
                
            match_score = await self.calculate_assistant_match(
                assistant_config,
                analysis
            )
            
            if match_score > 0.5:  # Threshold for considering an assistant suitable
                suitable_assistants.append({
                    **assistant_config,
                    "match_score": match_score
                })
        
        # Sort by match score
        suitable_assistants.sort(key=lambda x: x["match_score"], reverse=True)
        
        yield {
            "type": "assistants_found",
            "message": f"Found {len(suitable_assistants)} suitable assistants",
            "details": {
                "assistants": suitable_assistants
            }
        }

    async def stream_process(
        self,
        query: str,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process the query with real-time coordination and thinking."""
        try:
            # Step 1: Initial Analysis
            yield {
                "type": "thinking",
                "message": "🤔 Analyzing query requirements..."
            }
            
            requirements = await self.analyze_requirements(query)
            
            # Show analysis results
            yield {
                "type": "thinking",
                "message": f"""📊 Analysis complete:
- Needs specialists: {requirements['needs_specialists']}
- Primary expertise: {requirements['primary_expertise_needed']}
- Tools needed: {', '.join(requirements['required_tools'])}"""
            }
            
            # Step 2: Try Specialist First
            specialist_data = None
            if requirements['needs_specialists']:
                yield {
                    "type": "thinking",
                    "message": f"👥 Looking for specialists in {requirements['primary_expertise_needed']}..."
                }
                
                # Find specialists
                specialists = []
                for assistant in self.available_assistants:
                    if any(exp.lower() in requirements['primary_expertise_needed'].lower() 
                          for exp in assistant.get('expertise', [])):
                        specialists.append(assistant)
                
                if specialists:
                    specialist = specialists[0]
                    yield {
                        "type": "thinking",
                        "message": f"🤝 Consulting {specialist['name']}..."
                    }
                    
                    try:
                        # Create specialist agent
                        specialist_agent = await self.create_assistant(
                            specialist,
                            openai_api_key=self.model_manager.api_keys["openai"],
                            anthropic_api_key=self.model_manager.api_keys["anthropic"]
                        )
                        
                        # Get specialist input
                        specialist_data = await specialist_agent.process(query)
                        
                        yield {
                            "type": "thinking",
                            "message": f"📝 Received specialist input from {specialist['name']}"
                        }
                    except Exception as e:
                        yield {
                            "type": "thinking",
                            "message": f"⚠️ Error consulting specialist: {str(e)}"
                        }
            
            # Step 3: Web Search if needed (explicit request or no specialist/low confidence)
            web_data = None
            if requirements['needs_web_search'] or (
                not specialist_data and 
                requirements.get('confidence_without_web', 1.0) < 0.6
            ):
                yield {
                    "type": "thinking",
                    "message": "🌐 Additional information needed, performing web search..."
                }
                
                web_results = []
                for search_query in requirements['search_queries']:
                    yield {
                        "type": "thinking",
                        "message": f"🔍 Searching for: {search_query}"
                    }
                    
                    try:
                        result = await self.web_search(search_query)
                        web_results.append(result)
                    except Exception as e:
                        yield {
                            "type": "thinking",
                            "message": f"⚠️ Search error: {str(e)}"
                        }
                
                web_data = "\n\n".join(web_results)
                
                yield {
                    "type": "thinking",
                    "message": "✅ Web search complete"
                }
            
            # Step 4: Final Response Generation
            yield {
                "type": "thinking",
                "message": "✨ Generating comprehensive response..."
            }
            
            web_search_results = f"Web Search Results:\n{web_data}\n" if web_data else ""
            specialist_input = f"Specialist Input:\n{specialist_data}\n" if specialist_data else ""
            
            final_prompt = (
                f'Query: "{query}"\n\n'
                f'{specialist_input}'
                f'{web_search_results}\n'
                'Create a clear, comprehensive response that:\n'
                '1. Integrates all available information\n'
                '2. Provides accurate and up-to-date details\n'
                '3. Maintains professional tone\n'
                '4. Includes relevant context and explanations\n\n'
                'Follow these standards:\n'
                f'{json.dumps(self.quality_standards, indent=2)}'
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
                        "content": final_prompt
                    }
                ],
                temperature=temperature,
                stream=True
            ):
                if chunk.get("type") == "response":
                    yield {"type": "content", "content": chunk.get("content", "")}
            
            yield {
                "type": "thinking",
                "message": "✅ Response complete!"
            }
            
        except Exception as e:
            logger.error(f"Error in stream_process: {str(e)}")
            yield {"type": "error", "error": str(e)}

    async def web_search(self, query: str) -> str:
        """Perform a web search using the SerpAgent."""
        try:
            from .serp_agent import SerpAgent
            import os
            
            # Create SERP agent with API key from environment
            serp_agent = SerpAgent(
                openai_api_key=self.model_manager.api_keys["openai"],
                anthropic_api_key=self.model_manager.api_keys["anthropic"],
                serpapi_key=os.getenv('SERP_API_KEY')
            )
            
            # Process the query
            return await serp_agent.process(query)
            
        except Exception as e:
            logger.error(f"Error in web_search: {str(e)}")
            return f"Error performing web search: {str(e)}"

    async def process_simple_query(self, query: str, analysis: Dict[str, Any]) -> str:
        """Process a simple query using AI."""
        prompt = f"""
        Query: "{query}"
        Analysis: {json.dumps(analysis, indent=2)}
        
        Quality Standards to follow:
        {json.dumps(self.quality_standards, indent=2)}
        
        Communication Standards:
        {json.dumps(self.communication_standards['with_users'], indent=2)}
        
        Provide a direct and comprehensive response that:
        1. Addresses all aspects of the query
        2. Maintains appropriate expertise level
        3. Includes relevant details and context
        4. Follows the quality and communication standards
        """
        
        return await self.llm_call(
            prompt,
            temperature=0.7,
            max_tokens=500
        )

    async def consult_assistant(self, query: str, assistant: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Get response from a specific assistant."""
        prompt = f"""
        You are the {assistant['name']} assistant with expertise in {', '.join(assistant['expertise'])}.
        
        Query: "{query}"
        Analysis: {json.dumps(analysis, indent=2)}
        
        Your capabilities: {json.dumps(assistant['capabilities'], indent=2)}
        
        Quality Standards to follow:
        {json.dumps(self.quality_standards, indent=2)}
        
        Provide a response that:
        1. Focuses on your areas of expertise
        2. Maintains appropriate tone and technical level
        3. Includes specific recommendations and insights
        4. References relevant standards or best practices
        5. Follows the quality standards
        """
        
        return await self.llm_call(
            prompt,
            temperature=0.7,
            max_tokens=500
        )

    async def calculate_assistant_match(self, assistant: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """Calculate how well an assistant matches the query requirements."""
        match_prompt = f"""
        Assistant Configuration:
        {json.dumps(assistant, indent=2)}
        
        Query Analysis:
        {json.dumps(analysis, indent=2)}
        
        Calculate a match score between 0 and 1 based on:
        1. Expertise alignment with required areas
        2. Capability match with required capabilities
        3. Complexity level appropriateness
        4. Topic relevance to assistant's domain
        
        Return only the numeric score.
        """
        
        try:
            score_response = await self.llm_call(
                match_prompt,
                temperature=0.3,
                max_tokens=50
            )
            return float(score_response.strip())
        except (ValueError, TypeError):
            # Fallback to basic matching
            expertise_match = len(
                set(assistant.get("expertise", [])) &
                set(analysis.get("required_expertise", []))
            )
            capability_match = len(
                set(assistant.get("capabilities", [])) &
                set(analysis.get("required_capabilities", []))
            )
            return min(1.0, (expertise_match + capability_match) / max(
                1,
                len(analysis.get("required_expertise", [])) +
                len(analysis.get("required_capabilities", []))
            ))

    async def llm_call(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model_type: str = "reasoning",
        model_category: str = "reasoning"
    ) -> str:
        """Call the language model with a prompt and return the response."""
        try:
            # Select appropriate model
            model = None
            provider = None
            async for update in self.model_manager.select_model_with_progress(
                query=prompt,
                required_capabilities=["conversation"],
                temperature=temperature
            ):
                if update.get("type") == "model_selected":
                    model_info = update.get("model", {})
                    model = model_info.get("name")
                    provider = model_info.get("provider")
                    break
            
            if not model or not provider:
                raise ValueError("Failed to select model")
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": f"""You are {self.name}, {self.description}.
                    Follow these quality standards:
                    {json.dumps(self.quality_standards, indent=2)}
                    
                    Follow these communication standards:
                    {json.dumps(self.communication_standards, indent=2)}"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Get response
            response = None
            async for chunk in self.model_manager.call_with_tools(
                model=model,
                provider=provider,
                messages=messages,
                temperature=temperature,
                stream=False
            ):
                if chunk.get("type") == "response":
                    response = chunk
                    break
            
            if not response:
                raise ValueError("No response received from model")
            
            return response["content"]
            
        except Exception as e:
            logger.error(f"Error in llm_call: {str(e)}")
            raise

    async def create_assistant(
        self,
        config: Dict[str, Any],
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ) -> BaseAgent:
        """Create a new assistant from configuration."""
        from ..core.base_assistant import BaseAssistant
        
        class DynamicAssistant(BaseAssistant):
            def __init__(self, config, **kwargs):
                super().__init__(
                    name=config["name"],
                    description=config["description"],
                    **kwargs
                )
                self.expertise = config.get("expertise", [])
                self.capabilities = config.get("capabilities", [])
                self.max_complexity = config.get("max_complexity", 5)
                self.supported_tasks = config.get("supported_tasks", [])
                self.preferred_model = config.get("preferred_model")
                self.instructions = config.get("instructions", "")
                self.config = config
                
            async def analyze_query(self, query: str) -> float:
                """Analyze if this assistant can handle the query."""
                # Use AI to analyze query relevance
                analysis_prompt = f"""
                Given this query: "{query}"
                And my expertise in: {', '.join(self.expertise)}
                With capabilities: {', '.join(self.capabilities)}
                
                Calculate a confidence score (0-1) for how well I can handle this query.
                Consider:
                1. Topic relevance to expertise
                2. Required capabilities match
                3. Query complexity vs my max complexity ({self.max_complexity})
                
                Return only the numeric score.
                """
                
                try:
                    score_response = await self.llm_call(
                        analysis_prompt,
                        temperature=0.3,
                        max_tokens=50
                    )
                    return float(score_response.strip())
                except (ValueError, TypeError):
                    # Fallback to basic matching
                    expertise_words = set(' '.join(self.expertise).lower().split())
                    query_words = set(query.lower().split())
                    word_match = len(expertise_words & query_words)
                    return min(1.0, word_match / max(1, len(query_words)))

            async def can_handle(self, query: str) -> bool:
                """Check if this assistant can handle the query."""
                confidence = await self.analyze_query(query)
                return confidence > 0.5

            def get_context(self) -> Dict[str, Any]:
                """Return the assistant's context."""
                return {
                    "role": self.config.get("role", "specialist"),
                    "name": self.name,
                    "description": self.description,
                    "expertise": self.expertise,
                    "capabilities": self.capabilities,
                    "instructions": self.instructions
                }

            async def validate_response(self, response: Dict[str, Any]) -> bool:
                """Validate the response."""
                # Basic validation - ensure response has required fields
                if not isinstance(response, dict):
                    return False
                if "type" not in response or "content" not in response:
                    return False
                if not response["content"]:
                    return False
                return True

            async def process(self, query: str, **kwargs) -> str:
                """Process a query and return a response."""
                response_chunks = []
                async for chunk in self.stream_process(query, **kwargs):
                    if chunk["type"] == "content":
                        response_chunks.append(chunk["content"])
                return "".join(response_chunks)

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
                        "message": f"🔍 {self.name} analyzing query..."
                    }

                    # Prepare specialist prompt
                    prompt = f"""
                    As {self.name}, {self.config.get('role', 'Specialist')} with expertise in {', '.join(self.expertise)},
                    provide a response to: "{query}"

                    Follow these instructions:
                    {self.instructions}

                    Your expertise areas: {', '.join(self.expertise)}
                    Your capabilities: {', '.join(self.capabilities)}

                    Provide a detailed response that:
                    1. Focuses on your specific areas of expertise
                    2. Leverages your specialized knowledge
                    3. Provides actionable recommendations
                    4. Maintains professional tone
                    5. Includes relevant technical details when appropriate
                    """

                    yield {
                        "type": "thinking",
                        "message": f"💭 {self.name} formulating response..."
                    }

                    # Stream the response
                    async for chunk in self.model_manager.call_with_tools(
                        model=self.preferred_model or "gpt-4",
                        provider="openai",
                        messages=[
                            {
                                "role": "system",
                                "content": f"You are {self.name}, {self.description}."
                            },
                            {
                                "role": "user",
                                "content": prompt
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
                        "message": f"✅ {self.name}'s response complete"
                    }

                except Exception as e:
                    logger.error(f"Error in {self.name}'s stream_process: {str(e)}")
                    yield {
                        "type": "error",
                        "error": f"Error processing query: {str(e)}"
                    }

        # Create new assistant instance
        assistant = DynamicAssistant(
            config,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )
        
        return assistant
