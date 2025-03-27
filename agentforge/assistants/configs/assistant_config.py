from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class AssistantConfig(BaseModel):
    name: str
    description: str
    instructions: str
    model: str
    temperature: float = 0.7
    files: List[str] = []
    keywords: List[str] = []
    task_types: List[str] = []
    
    class Config:
        extra = "allow"

# Define your four specialized assistants
ASSISTANT_CONFIGS = {
    "construction_coordinator": AssistantConfig(
        name="Construction Coordinator",
        description="Specialized in managing construction projects and coordinating activities",
        instructions="You are a construction coordination expert focused on managing projects, documents, and stakeholder communication...",
        model="gpt-4-turbo-preview",
        keywords=["construction", "project", "schedule", "quality", "coordination", "document", "stakeholder", "contractor", "inspection", "permit"],
        task_types=["project_coordination", "document_management", "quality_control", "schedule_management", "stakeholder_communication"],
        files=["coordinator_guidelines.md", "safety_guidelines.md"]
    ),
    
    "construction_meeting": AssistantConfig(
        name="Construction Meeting Assistant",
        description="Specialized in managing construction meetings and documentation",
        instructions="You are a construction meeting expert focused on managing meetings, tracking actions, and documenting decisions...",
        model="claude-3-opus-20240229",
        keywords=["meeting", "agenda", "minutes", "action", "decision", "follow-up", "attendee", "discussion", "resolution"],
        task_types=["meeting_management", "action_tracking", "minutes_preparation", "follow_up_coordination", "decision_documentation"],
        files=["meeting_guidelines.md", "coordinator_guidelines.md"]
    ),
    
    "code_assistant": AssistantConfig(
        name="Code Assistant",
        description="Specialized in code analysis, review, and development",
        instructions="You are an expert programmer focused on code analysis, review, and development...",
        model="gpt-4-turbo-preview",
        keywords=["code", "programming", "debug", "function", "class", "implement"],
        task_types=["code_review", "debugging", "implementation"],
        files=["code_guidelines.md"]
    ),
    
    "data_assistant": AssistantConfig(
        name="Data Analysis Assistant",
        description="Specialized in data analysis and visualization",
        instructions="You are a data analysis expert focused on processing and visualizing data...",
        model="claude-3-opus-20240229",
        keywords=["data", "analysis", "visualization", "statistics", "graph", "plot"],
        task_types=["data_analysis", "visualization", "statistics"],
        files=["data_analysis_templates.md"]
    ),
    
    "research_assistant": AssistantConfig(
        name="Research Assistant",
        description="Specialized in academic research and literature review",
        instructions="You are a research expert focused on academic analysis and literature review...",
        model="claude-3-opus-20240229",
        keywords=["research", "paper", "study", "literature", "academic", "analysis"],
        task_types=["literature_review", "research_analysis", "paper_writing"],
        files=["research_guidelines.md"]
    ),
    
    "writing_assistant": AssistantConfig(
        name="Writing Assistant",
        description="Specialized in content creation and editing",
        instructions="You are a writing expert focused on content creation and editing...",
        model="gpt-4-turbo-preview",
        keywords=["write", "edit", "content", "article", "blog", "document"],
        task_types=["content_creation", "editing", "proofreading"],
        files=["writing_guidelines.md"]
    )
} 