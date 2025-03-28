from typing import Dict, Any, List, Optional, AsyncGenerator
import openai
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import json
import os

class ModelManager:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None
    ):
        self.openai_client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None
        self.anthropic_client = AsyncAnthropic(api_key=anthropic_api_key) if anthropic_api_key else None
        
        if not (self.openai_client or self.anthropic_client):
            raise ValueError("At least one of OpenAI or Anthropic API key must be provided")
        
        # Define available models and their capabilities
        self.models = {
            "claude-3-opus-20240229": {  # o3
                "provider": "anthropic",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling", "reasoning"],
                "max_tokens": 4096,
                "temperature_range": (0.0, 1.0),
                "alias": "o3",
                "priority": 1  # Highest priority
            },
            "claude-3-sonnet-20240229": {  # o1
                "provider": "anthropic",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling", "reasoning"],
                "max_tokens": 4096,
                "temperature_range": (0.0, 1.0),
                "alias": "o1",
                "priority": 2  # Second priority
            },
            "gpt-4-turbo-preview": {
                "provider": "openai",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling"],
                "max_tokens": 4096,
                "temperature_range": (0.0, 2.0),
                "priority": 3  # Lower priority
            }
        }

        # Create alias mapping
        self.model_aliases = {
            "o3": "claude-3-opus-20240229",
            "o1": "claude-3-sonnet-20240229"
        }
        
    def select_model(
        self,
        task_type: str,
        required_capabilities: List[str],
        preferred_model: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Select the most appropriate model based on task requirements and preferences"""
        
        # If preferred model is specified, try to resolve alias
        if preferred_model:
            if preferred_model in self.model_aliases:
                preferred_model = self.model_aliases[preferred_model]
            if preferred_model in self.models:
                model_specs = self.models[preferred_model]
                # Check if we have access to this model's provider
                if (model_specs["provider"] == "openai" and self.openai_client) or \
                   (model_specs["provider"] == "anthropic" and self.anthropic_client):
                    # Check if model has required capabilities
                    if all(cap in model_specs["capabilities"] for cap in required_capabilities):
                        return {
                            "name": preferred_model,
                            "provider": model_specs["provider"],
                            "max_tokens": model_specs["max_tokens"],
                            "temperature": min(max(temperature, model_specs["temperature_range"][0]), 
                                            model_specs["temperature_range"][1])
                        }
        
        # If no preferred model or preferred model not available, find suitable models
        suitable_models = []
        
        for model_name, specs in self.models.items():
            # Check if we have access to this model's provider
            if specs["provider"] == "openai" and not self.openai_client:
                continue
            if specs["provider"] == "anthropic" and not self.anthropic_client:
                continue
            
            # Check if model has all required capabilities
            if all(cap in specs["capabilities"] for cap in required_capabilities):
                suitable_models.append((model_name, specs))
        
        if not suitable_models:
            raise ValueError("No suitable model found for the given requirements")
        
        # Sort by priority (lower number = higher priority)
        suitable_models.sort(key=lambda x: x[1].get("priority", 999))
        
        # Return the highest priority suitable model
        selected_model, specs = suitable_models[0]
        
        return {
            "name": selected_model,
            "provider": specs["provider"],
            "max_tokens": specs["max_tokens"],
            "temperature": min(max(temperature, specs["temperature_range"][0]), 
                            specs["temperature_range"][1])
        }

    async def call_with_tools(
        self,
        model: Dict[str, Any],
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        stream: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Call the AI model with the given messages and tools."""
        try:
            if model["provider"] == "openai":
                async for chunk in self._call_openai(
                    model=model["name"],
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    stream=stream
                ):
                    yield chunk
            elif model["provider"] == "anthropic":
                async for chunk in self._call_anthropic(
                    model=model["name"],
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    stream=stream
                ):
                    yield chunk
            else:
                yield {
                    "type": "error",
                    "content": f"Unsupported model provider: {model['provider']}"
                }
        except Exception as e:
            yield {
                "type": "error",
                "content": f"{model['provider']} API error: {str(e)}"
            }

    async def _call_openai(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        stream: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Call OpenAI API with the given parameters."""
        try:
            if not self.openai_client:
                yield {
                    "type": "error",
                    "content": "OpenAI API key not provided"
                }
                return
                
            # Prepare parameters
            params = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            
            # Only add temperature if explicitly provided
            if temperature is not None:
                params["temperature"] = temperature
                
            # Add tools if provided
            if tools:
                params["tools"] = tools

            # Make API call
            response = await self.openai_client.chat.completions.create(**params)

            if stream:
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield {
                            "type": "response",
                            "content": chunk.choices[0].delta.content
                        }
            else:
                yield {
                    "type": "response",
                    "content": response.choices[0].message.content
                }
        except Exception as e:
            yield {
                "type": "error",
                "content": f"OpenAI API error: {str(e)}"
            }

    async def _call_anthropic(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        stream: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Call Anthropic API with the given parameters."""
        try:
            if not self.anthropic_client:
                yield {
                    "type": "error",
                    "content": "Anthropic API key not provided"
                }
                return
                
            # Convert messages to Anthropic format
            system_message = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
            user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
            
            # Prepare parameters
            params = {
                "model": model,
                "messages": [
                    {"role": "user", "content": content}
                    for content in user_messages
                ],
                "stream": stream
            }
            
            # Add system message if present
            if system_message:
                params["system"] = system_message
                
            # Only add temperature if explicitly provided
            if temperature is not None:
                params["temperature"] = temperature

            # Make API call
            response = await self.anthropic_client.messages.create(**params)

            if stream:
                async for chunk in response:
                    if chunk.delta.text:
                        yield {
                            "type": "response",
                            "content": chunk.delta.text
                        }
            else:
                yield {
                    "type": "response",
                    "content": response.content[0].text
                }
        except Exception as e:
            yield {
                "type": "error",
                "content": f"Anthropic API error: {str(e)}"
            }

    def _convert_to_anthropic_tools(self, openai_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI tool format to Anthropic format"""
        anthropic_tools = []
        for tool in openai_tools:
            if tool["type"] == "function":
                anthropic_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["function"]["name"],
                        "parameters": tool["function"]["parameters"],
                        "description": tool["function"].get("description", "")
                    }
                })
        return anthropic_tools
        
    def _convert_from_anthropic_tool_calls(self, anthropic_tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Anthropic tool calls to OpenAI format for consistency"""
        openai_tool_calls = []
        for call in anthropic_tool_calls:
            if call["type"] == "function":
                openai_tool_calls.append({
                    "type": "function",
                    "function": {
                        "name": call["function"]["name"],
                        "arguments": json.dumps(call["function"]["arguments"])
                    },
                    "id": call.get("id", "")
                })
        return openai_tool_calls 