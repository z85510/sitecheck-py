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
            # Reasoning Models (o-series)
            "o3-mini": {
                "provider": "openai",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling", "reasoning"],
                "max_tokens": 8192,
                "temperature_range": (0.0, 2.0),
                "alias": "o3-mini",
                "priority": 1,  # Highest priority
                "default_temperature": 0.1,
                "type": "reasoning",
                "category": "reasoning"
            },
            "o1": {
                "provider": "openai",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling", "reasoning"],
                "max_tokens": 8192,
                "temperature_range": (0.0, 2.0),
                "alias": "o1",
                "priority": 2,
                "default_temperature": 0.1,
                "type": "reasoning",
                "category": "reasoning"
            },
            "o1-mini": {
                "provider": "openai",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling"],
                "max_tokens": 8192,
                "temperature_range": (0.0, 2.0),
                "alias": "o1-mini",
                "priority": 3,
                "default_temperature": 0.1,
                "type": "default",
                "category": "reasoning"
            },
            "o1-pro": {
                "provider": "openai",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling", "reasoning"],
                "max_tokens": 16384,
                "temperature_range": (0.0, 2.0),
                "alias": "o1-pro",
                "priority": 4,
                "default_temperature": 0.1,
                "type": "reasoning",
                "category": "reasoning"
            },

            # Flagship Chat Models
            "gpt-4.5-preview": {
                "provider": "openai",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling", "reasoning"],
                "max_tokens": 32768,
                "temperature_range": (0.0, 2.0),
                "alias": "gpt-45",
                "priority": 5,
                "default_temperature": 0.1,
                "type": "reasoning",
                "category": "flagship"
            },
            "gpt-4o": {
                "provider": "openai",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling", "reasoning"],
                "max_tokens": 8192,
                "temperature_range": (0.0, 2.0),
                "alias": "gpt-4o",
                "priority": 6,
                "default_temperature": 0.1,
                "type": "reasoning",
                "category": "flagship"
            },

            # Cost-optimized Models
            "gpt-4o-mini": {
                "provider": "openai",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling"],
                "max_tokens": 8192,
                "temperature_range": (0.0, 2.0),
                "alias": "gpt-4o-mini",
                "priority": 7,
                "default_temperature": 0.1,
                "type": "default",
                "category": "cost-optimized"
            },

            # Older GPT Models
            "gpt-4-turbo": {
                "provider": "openai",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling", "reasoning"],
                "max_tokens": 8192,
                "temperature_range": (0.0, 2.0),
                "alias": "gpt-4t",
                "priority": 8,
                "default_temperature": 0.1,
                "type": "reasoning",
                "category": "legacy"
            },
            "gpt-4": {
                "provider": "openai",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling", "reasoning"],
                "max_tokens": 8192,
                "temperature_range": (0.0, 2.0),
                "alias": "gpt-4",
                "priority": 9,
                "default_temperature": 0.1,
                "type": "reasoning",
                "category": "legacy"
            },

            # Claude Models
            "claude-3-opus-20240229": {
                "provider": "anthropic",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling", "reasoning"],
                "max_tokens": 4096,
                "temperature_range": (0.0, 1.0),
                "alias": "c3-opus",
                "priority": 10,
                "default_temperature": 0.1,
                "type": "reasoning",
                "category": "claude"
            },
            "claude-3-sonnet-20240229": {
                "provider": "anthropic",
                "capabilities": ["analysis", "conversation", "task_processing", "safety", "compliance", "tool_calling"],
                "max_tokens": 4096,
                "temperature_range": (0.0, 1.0),
                "alias": "c3-sonnet",
                "priority": 11,
                "default_temperature": 0.1,
                "type": "default",
                "category": "claude"
            },
            "claude-3-haiku-20240229": {
                "provider": "anthropic",
                "capabilities": ["analysis", "conversation", "task_processing"],
                "max_tokens": 4096,
                "temperature_range": (0.0, 1.0),
                "alias": "c3-haiku",
                "priority": 12,
                "default_temperature": 0.1,
                "type": "default",
                "category": "claude"
            }
        }

        # Create alias mapping
        self.model_aliases = {
            # Reasoning Models
            "o3-mini": "o3-mini",
            "o1": "o1",
            "o1-mini": "o1-mini",
            "o1-pro": "o1-pro",
            
            # Flagship Models
            "gpt-45": "gpt-4.5-preview",
            "gpt-4o": "gpt-4o",
            
            # Cost-optimized Models
            "gpt-4o-mini": "gpt-4o-mini",
            
            # Legacy Models
            "gpt-4t": "gpt-4-turbo",
            "gpt-4": "gpt-4",
            
            # Claude Models
            "c3-opus": "claude-3-opus-20240229",
            "c3-sonnet": "claude-3-sonnet-20240229",
            "c3-haiku": "claude-3-haiku-20240229"
        }
        
    def select_model(
        self,
        task_type: str,
        required_capabilities: List[str],
        preferred_model: Optional[str] = None,
        model_type: Optional[str] = None,  # "reasoning" or "default"
        model_category: Optional[str] = None,  # "reasoning", "flagship", "cost-optimized", "legacy", "claude"
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Select the most appropriate model based on task requirements and preferences"""
        
        # Default to gpt-4 if no specific requirements
        if not required_capabilities and not model_type and not model_category:
            return {
                "name": "gpt-4",
                "provider": "openai",
                "max_tokens": 8192,
                "temperature": temperature if temperature is not None else 0.7,
                "type": "default",
                "category": "legacy"
            }
        
        # If preferred model is specified, try to resolve alias
        if preferred_model:
            if preferred_model in self.model_aliases:
                preferred_model = self.model_aliases[preferred_model]
            if preferred_model in self.models:
                model_specs = self.models[preferred_model]
                # Check if we have access to this model's provider
                if (model_specs["provider"] == "openai" and self.openai_client) or \
                   (model_specs["provider"] == "anthropic" and self.anthropic_client):
                    # Check if model has required capabilities and matches type/category if specified
                    if all(cap in model_specs["capabilities"] for cap in required_capabilities) and \
                       (not model_type or model_specs.get("type") == model_type) and \
                       (not model_category or model_specs.get("category") == model_category):
                        return {
                            "name": preferred_model,
                            "provider": model_specs["provider"],
                            "max_tokens": model_specs["max_tokens"],
                            "temperature": temperature if temperature is not None else model_specs.get("default_temperature", 0.7),
                            "type": model_specs.get("type", "default"),
                            "category": model_specs.get("category", "default")
                        }
        
        # If no preferred model or preferred model not available, find suitable models
        suitable_models = []
        
        for model_name, specs in self.models.items():
            # Check if we have access to this model's provider
            if specs["provider"] == "openai" and not self.openai_client:
                continue
            if specs["provider"] == "anthropic" and not self.anthropic_client:
                continue
            
            # Check if model has all required capabilities and matches type/category if specified
            if all(cap in specs["capabilities"] for cap in required_capabilities) and \
               (not model_type or specs.get("type") == model_type) and \
               (not model_category or specs.get("category") == model_category):
                suitable_models.append((model_name, specs))
        
        # If no suitable models found, fall back to gpt-4
        if not suitable_models:
            return {
                "name": "gpt-4",
                "provider": "openai",
                "max_tokens": 8192,
                "temperature": temperature if temperature is not None else 0.7,
                "type": "default",
                "category": "legacy"
            }
        
        # Sort by priority (lower number = higher priority)
        suitable_models.sort(key=lambda x: x[1].get("priority", 999))
        
        # Return the highest priority suitable model
        selected_model, specs = suitable_models[0]
        
        return {
            "name": selected_model,
            "provider": specs["provider"],
            "max_tokens": specs["max_tokens"],
            "temperature": temperature if temperature is not None else specs.get("default_temperature", 0.7),
            "type": specs.get("type", "default"),
            "category": specs.get("category", "default")
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
                
            # Map model names to actual OpenAI model names
            model_mapping = {
                "o3-mini": "gpt-4-0125-preview",  # Latest GPT-4 Turbo
                "o1": "gpt-4",
                "o1-mini": "gpt-4",
                "o1-pro": "gpt-4",
                "gpt-4o": "gpt-4",
                "gpt-4o-mini": "gpt-4",
                "gpt-4-turbo": "gpt-4-0125-preview",
                "gpt-4": "gpt-4",
                "gpt-4.5-preview": "gpt-4-0125-preview"
            }
            
            actual_model = model_mapping.get(model, model)
                
            # Prepare parameters
            params = {
                "model": actual_model,
                "messages": messages,
                "stream": stream
            }
            
            # Only add temperature if explicitly provided
            if temperature is not None:
                params["temperature"] = temperature
                
            # Add tools if provided
            if tools:
                params["tools"] = tools

            try:
                # Make API call
                response = await self.openai_client.chat.completions.create(**params)

                if stream:
                    content_buffer = ""
                    async for chunk in response:
                        # Get content from the chunk
                        content = chunk.choices[0].delta.content
                        
                        # If we have content, add it to buffer
                        if content:
                            content_buffer += content
                            yield {
                                "type": "response",
                                "content": content
                            }
                    
                    # If we got no content at all, yield a default response
                    if not content_buffer:
                        yield {
                            "type": "response",
                            "content": "Hello! I'm here to help. What can I assist you with today?"
                        }
                else:
                    content = response.choices[0].message.content
                    if content:
                        yield {
                            "type": "response",
                            "content": content
                        }
                    else:
                        yield {
                            "type": "response",
                            "content": "Hello! I'm here to help. What can I assist you with today?"
                        }
            except openai.BadRequestError as e:
                # Handle specific OpenAI errors
                error_message = str(e)
                if "model does not exist" in error_message.lower():
                    yield {
                        "type": "error",
                        "content": f"Model '{model}' is not available. Using default model instead.",
                    }
                    # Retry with default model
                    params["model"] = "gpt-4"
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
                else:
                    raise  # Re-raise if it's a different BadRequestError
                    
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")  # Log the error for debugging
            yield {
                "type": "response",
                "content": "Hello! I'm here to help. What can I assist you with today?"
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