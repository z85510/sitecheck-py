from typing import Dict, Any, AsyncGenerator, Optional, List
from ..core.base_assistant import BaseAssistant
import json

class SafetyAssistant(BaseAssistant):
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        base_path: str = "agentforge"
    ):
        super().__init__(
            name="Safety Assistant",
            description="Expert in construction site safety and compliance",
            role="""You are the SiteCheck Auditor Specialist, dedicated to ensuring health and safety 
            excellence in construction sites. You guide Health and Safety Administrators (HSAs) and 
            Health and Safety Coordinators (HSCs) in complying with regional Audit Guides.""",
            task_types=[
                "safety_audit",
                "compliance_check",
                "emergency_planning",
                "safety_inspection",
                "policy_review"
            ],
            keywords=[
                "safety",
                "audit",
                "compliance",
                "inspection",
                "emergency",
                "COR",
                "policy"
            ],
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
            base_path=base_path
        )

    async def analyze_query(self, query: str) -> float:
        """Analyze if this assistant should handle the safety-related query"""
        # Check if query contains safety-related keywords
        safety_indicators = [
            "safety", "audit", "compliance", "inspection",
            "emergency", "COR", "policy", "hazard",
            "risk", "incident", "accident", "protection"
        ]
        
        score = sum(1 for keyword in safety_indicators if keyword.lower() in query.lower())
        return min(score / 3, 1.0)  # Normalize score between 0 and 1

    async def stream_process(
        self,
        query: str,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process safety-related queries following the COR Audit Guide structure"""
        
        # 1. Break down the query into manageable sub-tasks
        yield {
            "type": "thinking",
            "content": "🔍 Breaking down query into safety-related sub-tasks...",
            "agent": self.name
        }

        # Select model with safety-specific capabilities
        model = self.model_manager.select_model(
            task_type="safety_audit",
            required_capabilities=["safety", "compliance"],
            temperature=kwargs.get("temperature", 0.7)
        )

        # Prepare messages with safety context
        messages = [
            {
                "role": "system",
                "content": f"""{self.role}

Follow this process for safety-related queries:
1. Break down the query into manageable sub-tasks
2. Consult relevant COR Audit Guide sections
3. Compile comprehensive answers with citations
4. Provide actionable steps and compliance checks

Task Types: {', '.join(self.task_types)}"""
            },
            {
                "role": "user",
                "content": query
            }
        ]

        # Generate safety-focused response
        async for chunk in self.model_manager.call_with_tools(
            model=model,
            messages=messages,
            stream=True,
            **kwargs
        ):
            if chunk["type"] == "response":
                yield {
                    "type": "response",
                    "content": chunk["content"],
                    "agent": self.name,
                    "citations": [],  # Would be populated in a full implementation
                    "actionable_steps": [],  # Would be populated in a full implementation
                    "compliance_check": True  # Would be validated in a full implementation
                }
            else:
                yield chunk

    def get_context(self) -> Dict[str, Any]:
        """Return the safety assistant's context"""
        return {
            "name": self.name,
            "description": self.description,
            "role": self.role,
            "task_types": self.task_types,
            "keywords": self.keywords,
            "capabilities": [
                "COR Audit Guide expertise",
                "Safety compliance assessment",
                "Emergency planning guidance",
                "Policy review and development",
                "Inspection protocols"
            ]
        }

    async def validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate if the response meets safety standards"""
        required_elements = [
            "citations",  # Must include relevant COR citations
            "actionable_steps",  # Must include clear next steps
            "compliance_check"  # Must verify compliance with standards
        ]
        
        return all(element in response for element in required_elements) 