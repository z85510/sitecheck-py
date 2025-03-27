import aiohttp
from typing import Optional
from dataclasses import dataclass
from time import perf_counter

@dataclass
class Response:
    status_code: int
    headers: dict
    content: bytes
    elapsed_time: float

class HttpClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        
    async def get(self, url: str) -> Response:
        """Perform GET request and return response with timing."""
        start_time = perf_counter()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=self.timeout) as response:
                content = await response.read()
                elapsed = perf_counter() - start_time
                
                return Response(
                    status_code=response.status,
                    headers=dict(response.headers),
                    content=content,
                    elapsed_time=elapsed
                )