from typing import Any, Dict, Optional
from anthropic import Anthropic
from ..core.base_agent import BaseAgent

class ClaudeAgent(BaseAgent):
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.7,
        name: str = "Claude Assistant",
        description: str = "A sophisticated AI assistant powered by Anthropic's Claude"
    ):
        super().__init__(name, description)
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature

    async def process(self, query: str, **kwargs) -> str:
        try:
            response = await self.client.messages.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": query
                }],
                system=self.description,
                temperature=self.temperature,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            return f"Error processing query with Claude: {str(e)}"

    def can_handle(self, query: str) -> float:
        # Claude is particularly good at complex reasoning and analysis
        # You might want to implement more sophisticated logic here
        return 0.9 if any(keyword in query.lower() for keyword in 
            ['analyze', 'explain', 'compare', 'evaluate', 'reason']) else 0.7 