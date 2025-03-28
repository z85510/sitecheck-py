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