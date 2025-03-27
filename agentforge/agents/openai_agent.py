from typing import Any, Dict, Optional
import openai
from ..core.base_agent import BaseAgent

class OpenAIAgent(BaseAgent):
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        name: str = "OpenAI Assistant",
        description: str = "A versatile AI assistant powered by OpenAI's models"
    ):
        super().__init__(name, description)
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    async def process(self, query: str, **kwargs) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.description},
                    {"role": "user", "content": query}
                ],
                temperature=self.temperature,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error processing query with OpenAI: {str(e)}"

    def can_handle(self, query: str) -> float:
        # OpenAI is versatile and can handle most queries
        # You might want to implement more sophisticated logic here
        return 0.8 