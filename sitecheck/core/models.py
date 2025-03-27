from typing import Dict, List, Optional
from pydantic import BaseModel

class CheckResult(BaseModel):
    url: str
    status: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    headers: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    
    def summary(self) -> str:
        """Return a human-readable summary of the check results."""
        if self.status == "error":
            return f"Error checking {self.url}: {self.error}"
            
        return f"""
        URL: {self.url}
        Status: {self.status_code}
        Response Time: {self.response_time:.2f}s
        Headers: {len(self.headers or {})} present
        """.strip()