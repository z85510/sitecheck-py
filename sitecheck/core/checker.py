from typing import Dict, List, Optional
from urllib.parse import urlparse

from ..utils.http import HttpClient
from .models import CheckResult

class SiteChecker:
    def __init__(self, url: str, timeout: int = 30):
        self.url = url
        self.timeout = timeout
        self.client = HttpClient(timeout=timeout)
        
    async def analyze(self) -> CheckResult:
        """Analyze the website and return comprehensive results."""
        parsed_url = urlparse(self.url)
        if not parsed_url.scheme:
            self.url = f"https://{self.url}"
            
        result = CheckResult(
            url=self.url,
            status="pending"
        )
        
        try:
            response = await self.client.get(self.url)
            result.status = "success"
            result.response_time = response.elapsed_time
            result.status_code = response.status_code
            result.headers = dict(response.headers)
            
            # Add more analysis here
            
        except Exception as e:
            result.status = "error"
            result.error = str(e)
            
        return result