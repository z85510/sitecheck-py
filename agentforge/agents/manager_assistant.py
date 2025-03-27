from typing import Dict, Any, AsyncGenerator, Optional, List
from ..core.base_assistant import BaseAssistant
import json

class ManagerAssistant(BaseAssistant):
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ):
        super().__init__(
            name="SiteCheck Manager",
            description="Leader of the AI Assistants team in the SiteCheck product",
            role="""You are the SiteCheck Manager Agent, the leader of the AI Assistants team directly in the SiteCheck product! 
            You are the smartest and most knowledgeable assistant in your team, and it is your responsibility to interact with 
            the user and then work with your team of AI specialists to delegate, review and revise work and give a final output 
            to your user that is guaranteed to be of the highest quality.""",
            task_types=[
                "task_delegation",
                "quality_review",
                "team_coordination",
                "user_interaction",
                "document_management"
            ],
            keywords=[
                "manage",
                "coordinate",
                "review",
                "delegate",
                "quality",
                "team",
                "project"
            ],
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )
        
        # Initialize Info Stack layers
        self.expert_knowledge_bases = {}  # EKB - Specialist vector database storage
        self.company_knowhow = {}         # CKH - Company uploaded files
        self.user_project_files = {}      # UPF - User uploaded files
        
        # Initialize team roster
        self.team_roster = {
            "safetymeetingwriter": {
                "name": "Safety Meeting Writer",
                "expertise": ["toolbox_meetings", "safety_regulations", "meeting_structure"],
                "capabilities": ["create_meetings", "integrate_regulations", "test_questions"]
            },
            "incidentinvestigator": {
                "name": "Incident Investigator",
                "expertise": ["incident_investigation", "safety_analysis", "compliance"],
                "capabilities": ["investigate_incidents", "analyze_safety", "recommend_improvements"]
            },
            "complianceadvisor": {
                "name": "Compliance Advisor",
                "expertise": ["safety_compliance", "regulations", "guidelines"],
                "capabilities": ["review_documents", "clarify_regulations", "provide_advice"]
            },
            "safetyauditor": {
                "name": "Safety Auditor",
                "expertise": ["safety_audits", "cor_compliance", "emergency_planning"],
                "capabilities": ["conduct_audits", "review_policies", "assess_compliance"]
            },
            "productsupport": {
                "name": "Product Support",
                "expertise": ["product_usage", "account_management", "user_support"],
                "capabilities": ["setup_assistance", "user_training", "technical_support"]
            }
        }

    async def analyze_query(self, query: str) -> float:
        """Always returns 1.0 as the Manager can handle any query for analysis and delegation"""
        return 1.0

    async def stream_process(
        self,
        query: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process queries following the systematic routine"""
        
        # Step 1: Check query comprehensiveness
        yield {
            "type": "thinking",
            "content": "🤔 Analyzing your request for clarity and completeness...",
            "agent": self.name
        }

        # Select model for analysis
        model = self.model_manager.select_model(
            task_type="analysis",
            required_capabilities=["analysis", "task_processing"],
            temperature=0.7
        )

        # Prepare analysis messages
        analysis_messages = [
            {
                "role": "system",
                "content": f"""You are the SiteCheck Manager analyzing user requests. 
                Determine if the request is:
                1. Clear and complete
                2. Within scope of the team's capabilities
                3. Requires any Company Know-How (CKH) files
                4. Can be handled directly or needs specialist assistance
                
                For simple greetings or general questions not related to construction,
                respond that you will handle it directly."""
            },
            {
                "role": "user",
                "content": query
            }
        ]

        # Get analysis
        analysis_result = None
        async for chunk in self.model_manager.call_with_tools(
            model=model,
            messages=analysis_messages,
            stream=True
        ):
            if chunk["type"] == "response":
                yield {
                    "type": "thinking",
                    "content": f"💭 {chunk['content']}",
                    "agent": self.name
                }
                analysis_result = chunk["content"]

        # For general greetings or non-construction queries, handle directly
        if (
            analysis_result and (
                "not construction-related" in analysis_result.lower() or
                "handle directly" in analysis_result.lower() or
                query.lower().strip() in ["hello", "hi", "hey"]
            )
        ):
            # Select model for general response
            model = self.model_manager.select_model(
                task_type="conversation",
                required_capabilities=["conversation"],
                temperature=0.7
            )
            
            # Prepare messages for general response
            messages = [
                {
                    "role": "system",
                    "content": """You are the SiteCheck Manager, a friendly and professional assistant.
                    For general queries and greetings, provide warm, welcoming responses while maintaining professionalism.
                    Introduce yourself as the SiteCheck Manager when appropriate."""
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
            
            # Generate and stream response
            async for chunk in self.model_manager.call_with_tools(
                model=model,
                messages=messages,
                stream=True
            ):
                if chunk["type"] == "response":
                    yield {
                        "type": "response",
                        "content": chunk["content"],
                        "agent": self.name
                    }
            return

        # Step 2: Check for relevant CKH files
        if "requires_ckh" in analysis_result.lower():
            yield {
                "type": "thinking",
                "content": "🔍 Checking for relevant company knowledge files...",
                "agent": self.name
            }
            # Implementation would search through CKH files
            # For now, we'll assume no CKH files needed

        # Step 3: Determine if specialist needed
        if "needs_specialist" in analysis_result.lower():
            # Select appropriate specialist(s)
            specialists = self._select_specialists(query, analysis_result)
            
            # If no specialists selected (non-construction query), handle directly
            if not specialists:
                # Select model for general response
                model = self.model_manager.select_model(
                    task_type="conversation",
                    required_capabilities=["conversation"],
                    temperature=0.7
                )
                
                # Prepare messages for general response
                messages = [
                    {
                        "role": "system",
                        "content": """You are a helpful general-purpose assistant.
                        Provide clear, concise, and friendly responses to general queries.
                        Keep responses professional but conversational."""
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ]
                
                # Generate and stream response
                async for chunk in self.model_manager.call_with_tools(
                    model=model,
                    messages=messages,
                    stream=True
                ):
                    if chunk["type"] == "response":
                        yield {
                            "type": "response",
                            "content": chunk["content"],
                            "agent": self.name
                        }
                return
            
            # Handle construction-related queries with specialists
            for specialist_id, tasks in specialists.items():
                yield {
                    "type": "delegation",
                    "content": f"Delegating to {self.team_roster[specialist_id]['name']}...",
                    "agent": self.name
                }
                
                # Process with specialist
                specialist_response = await self._process_with_specialist(
                    specialist_id=specialist_id,
                    tasks=tasks,
                    query=query,
                    **kwargs
                )
                
                # Review specialist's work
                yield {
                    "type": "review",
                    "content": "Reviewing specialist's work for quality...",
                    "agent": self.name
                }
                
                # If review passes, include in final response
                if await self._validate_specialist_response(specialist_response):
                    yield {
                        "type": "response",
                        "content": specialist_response["content"],
                        "agent": self.name
                    }
                else:
                    # Request revision
                    yield {
                        "type": "revision",
                        "content": "Requesting revision from specialist...",
                        "agent": self.name
                    }
                    # Implementation would handle revision process
        else:
            # Handle directly
            yield {
                "type": "response",
                "content": "I'll handle this request directly...",
                "agent": self.name
            }
            # Implementation would handle direct response

    def get_context(self) -> Dict[str, Any]:
        """Return the manager's context"""
        return {
            "name": self.name,
            "description": self.description,
            "role": self.role,
            "task_types": self.task_types,
            "keywords": self.keywords,
            "team_roster": self.team_roster,
            "capabilities": [
                "Task delegation and coordination",
                "Quality review and assurance",
                "Team management",
                "Document handling across Info Stack",
                "Direct task completion for basic requests"
            ]
        }

    async def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate if a response meets quality standards"""
        required_elements = [
            "content",          # Must have actual content
            "is_complete",      # Must indicate if response is complete
            "is_accurate",      # Must be verified for accuracy
            "is_practical",     # Must be actionable/practical
            "follows_policy"    # Must adhere to company policies
        ]
        
        return all(element in response for element in required_elements)

    def _select_specialists(self, query: str, analysis: str) -> Dict[str, List[str]]:
        """Select appropriate specialists based on query and analysis"""
        # First check if this is a construction-related query
        construction_keywords = {
            "safety": ["safetymeetingwriter", "safetyauditor"],
            "meeting": ["safetymeetingwriter"],
            "toolbox": ["safetymeetingwriter"],
            "incident": ["incidentinvestigator"],
            "investigation": ["incidentinvestigator"],
            "compliance": ["complianceadvisor", "safetyauditor"],
            "regulation": ["complianceadvisor"],
            "audit": ["safetyauditor"],
            "cor": ["safetyauditor"],
            "product": ["productsupport"],
            "account": ["productsupport"],
            "setup": ["productsupport"]
        }
        
        # Check if query is construction-related
        if "not construction-related" in analysis.lower():
            # For non-construction queries, return empty dict to trigger direct handling
            return {}
            
        # For construction queries, find matching specialists
        specialists = {}
        query_lower = query.lower()
        
        # Check each keyword against the query
        for keyword, specialist_ids in construction_keywords.items():
            if keyword in query_lower:
                for specialist_id in specialist_ids:
                    if specialist_id not in specialists:
                        specialists[specialist_id] = []
                    # Add relevant tasks based on the specialist's capabilities
                    specialists[specialist_id].extend(
                        [cap for cap in self.team_roster[specialist_id]["capabilities"]
                         if any(kw in query_lower for kw in cap.split("_"))]
                    )
        
        # Remove duplicates from task lists
        for specialist_id in specialists:
            specialists[specialist_id] = list(set(specialists[specialist_id]))
            
        return specialists

    async def _process_with_specialist(
        self,
        specialist_id: str,
        tasks: List[str],
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process tasks with a specialist"""
        # Implementation would handle specialist interaction
        return {
            "type": "response",
            "content": "Specialist response placeholder",
            "is_complete": True,
            "is_accurate": True,
            "is_practical": True,
            "follows_policy": True
        }

    async def _validate_specialist_response(self, response: Dict[str, Any]) -> bool:
        """Validate a specialist's response"""
        # Implementation would check response quality
        return True 