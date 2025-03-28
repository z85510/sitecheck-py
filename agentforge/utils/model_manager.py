from typing import Dict, Any, List, Optional, AsyncGenerator, Tuple, Union
import logging
import json
from openai import AsyncOpenAI, BadRequestError
from anthropic import AsyncAnthropic
import os

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages AI model interactions and API keys."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None
    ):
        """Initialize the model manager with API keys."""
        self.api_keys = {
            "openai": openai_api_key,
            "anthropic": anthropic_api_key
        }
        
        # Initialize OpenAI client if key is provided
        self.openai_client = None
        if openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=openai_api_key)
            
        # Initialize Anthropic client if key is provided
        self.anthropic_client = None
        if anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=anthropic_api_key)
            
        # Map model names to actual model identifiers
        self.model_mapping = {
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
        
        # Ensure at least one API key is provided
        if not any(self.api_keys.values()):
            raise ValueError("At least one of OpenAI or Anthropic API key must be provided")
            
        # Initialize available models
        self.available_models = {
            "openai": {
                "gpt-4": {
                    "type": "chat",
                    "category": "openai",
                    "capabilities": ["conversation", "analysis", "creation"]
                },
                "gpt-3.5-turbo": {
                    "type": "chat",
                    "category": "openai",
                    "capabilities": ["conversation", "analysis"]
                }
            },
            "anthropic": {
                "claude-2": {
                    "type": "chat",
                    "category": "anthropic",
                    "capabilities": ["conversation", "analysis", "creation"]
                },
                "claude-instant-1": {
                    "type": "chat",
                    "category": "anthropic",
                    "capabilities": ["conversation"]
                }
            }
        }
        
        # Track active models
        self.active_models = {}
        for provider, key in self.api_keys.items():
            if key:
                self.active_models[provider] = self.available_models[provider]

    def set_api_key(self, provider: str, key: str) -> None:
        """Set an API key for a provider.
        
        Args:
            provider: The provider name (e.g., "openai", "anthropic")
            key: The API key
        """
        if provider not in ["openai", "anthropic"]:
            raise ValueError(f"Unsupported provider: {provider}")
            
        self.api_keys[provider] = key
        if key:
            self.active_models[provider] = self.available_models[provider]
        elif provider in self.active_models:
            del self.active_models[provider]

    async def select_model(
        self,
        query: str = None,
        preferred_model: str = None,
        required_capabilities: List[str] = None,
        temperature: float = 0.7,
    ) -> Tuple[str, str]:
        """
        Legacy method for backward compatibility.
        Selects the most appropriate model based on the query and requirements.
        """
        async for update in self.select_model_with_progress(
            query=query,
            preferred_model=preferred_model,
            required_capabilities=required_capabilities,
            temperature=temperature
        ):
            if update.get("type") == "model_selected":
                model_info = update.get("model", {})
                return model_info.get("name"), model_info.get("provider")
        
        # Fallback to default model if no model was selected
        return "gpt-4", "openai"  # Default to GPT-4 if available

    async def select_model_with_progress(
        self,
        query: Optional[str] = None,
        task_type: Optional[str] = None,
        required_capabilities: Optional[List[str]] = None,
        temperature: float = 0.7,
        preferred_model: Optional[str] = None,
        model_type: Optional[str] = None,
        model_category: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Select the best model for a task with progress updates."""
        yield {
            "type": "workflow",
            "step": "init",
            "content": "🔄 Initializing model selection process..."
        }

        # If preferred model is specified and available, use it
        if preferred_model:
            yield {
                "type": "workflow",
                "step": "check_preferred",
                "content": f"🔍 Checking availability of preferred model: {preferred_model}"
            }
            for provider, models in self.active_models.items():
                if preferred_model in models:
                    yield {
                        "type": "workflow",
                        "step": "selected",
                        "content": f"✅ Selected preferred model: {preferred_model} from {provider}"
                    }
                    yield {
                        "type": "model_selected",
                        "model": {
                            "name": preferred_model,
                            "provider": provider,
                            "temperature": temperature
                        }
                    }
                    return

        yield {
            "type": "workflow",
            "step": "filtering",
            "content": "🔍 Filtering available models based on requirements..."
        }
                    
        # Filter models by type and category if specified
        available_models = {}
        for provider, models in self.active_models.items():
            for model_name, model_info in models.items():
                if (not model_type or model_info["type"] == model_type) and \
                   (not model_category or model_info["category"] == model_category):
                    available_models[model_name] = {
                        "info": model_info,
                        "provider": provider
                    }

        # If no models match filters, use all active models
        if not available_models:
            yield {
                "type": "workflow",
                "step": "fallback",
                "content": "⚠️ No models match specific filters, considering all available models..."
            }
            for provider, models in self.active_models.items():
                for model_name, model_info in models.items():
                    available_models[model_name] = {
                        "info": model_info,
                        "provider": provider
                    }

        # If still no models available, raise error
        if not available_models:
            yield {
                "type": "workflow",
                "step": "error",
                "content": "❌ Error: No models available with current API keys"
            }
            raise ValueError("No models available with current API keys")

        # Filter by required capabilities
        if required_capabilities:
            yield {
                "type": "workflow",
                "step": "capabilities",
                "content": f"🔍 Checking models for required capabilities: {', '.join(required_capabilities)}"
            }
            capable_models = {}
            for model_name, model_info in available_models.items():
                if all(cap in model_info["info"]["capabilities"] for cap in required_capabilities):
                    capable_models[model_name] = model_info
            available_models = capable_models or available_models

        yield {
            "type": "workflow",
            "step": "selecting",
            "content": "🎯 Selecting optimal model from available options..."
        }

        # Select the most capable model (prefer GPT-4 or Claude-2)
        preferred_models = ["gpt-4", "claude-2", "gpt-3.5-turbo", "claude-instant-1"]
        for model in preferred_models:
            if model in available_models:
                yield {
                    "type": "workflow",
                    "step": "selected",
                    "content": f"✅ Selected model: {model} from {available_models[model]['provider']}"
                }
                yield {
                    "type": "model_selected",
                    "model": {
                        "name": model,
                        "provider": available_models[model]["provider"],
                        "temperature": temperature
                    }
                }
                return

        # If no preferred models available, use first available
        model_name = next(iter(available_models))
        yield {
            "type": "workflow",
            "step": "fallback_selected",
            "content": f"⚠️ Selected fallback model: {model_name} from {available_models[model_name]['provider']}"
        }
        yield {
            "type": "model_selected",
            "model": {
                "name": model_name,
                "provider": available_models[model_name]["provider"],
                "temperature": temperature
            }
        }

    async def call_with_tools(
        self,
        model: Union[str, Dict[str, Any]],
        provider: Optional[str] = None,
        messages: List[Dict[str, str]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        stream: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Call the AI model with tools."""
        try:
            # Handle model parameter
            if isinstance(model, dict):
                model_name = model.get("name")
                provider = model.get("provider")
                if not model_name or not provider:
                    raise ValueError("Model dictionary must contain 'name' and 'provider' keys")
            else:
                model_name = model
                if not provider:
                    # Try to determine provider from model name
                    if model_name.startswith("gpt-"):
                        provider = "openai"
                    elif model_name.startswith("claude-"):
                        provider = "anthropic"
                    else:
                        raise ValueError(f"Could not determine provider for model: {model_name}")

            # Map model name if needed
            if model_name in self.model_mapping:
                model_name = self.model_mapping[model_name]

            yield {
                "type": "workflow",
                "step": "api_call",
                "content": f"🔄 Calling {provider} API with model {model_name}..."
            }

            if provider == "openai":
                if not self.openai_client:
                    raise ValueError("OpenAI API key not set")
                async for chunk in self._call_openai(
                    model=model_name,
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    stream=stream
                ):
                    yield chunk
            elif provider == "anthropic":
                if not self.anthropic_client:
                    raise ValueError("Anthropic API key not set")
                async for chunk in self._call_anthropic(
                    model=model_name,
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    stream=stream
                ):
                    yield chunk
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        except Exception as e:
            yield {
                "type": "error",
                "content": f"❌ API call error: {str(e)}"
            }
            logger.error(f"Error in call_with_tools: {str(e)}")
            raise

    async def _call_openai(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        stream: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Call OpenAI API with the given parameters."""
        if not self.openai_client:
            raise ValueError("OpenAI API key not set")
            
        # Map model name to actual model identifier
        actual_model = self.model_mapping.get(model, model)
            
        # Prepare parameters
        params = {
            "model": actual_model,
            "messages": messages,
            "temperature": temperature if temperature is not None else 0.7,
            "stream": stream
        }
        
        # Add tools if provided
        if tools:
            params["tools"] = tools

        try:
            # Make API call
            response = await self.openai_client.chat.completions.create(**params)

            if stream:
                content_buffer = ""
                word_buffer = ""
                async for chunk in response:
                    # Get content from the chunk
                    delta = chunk.choices[0].delta
                    content = delta.content if hasattr(delta, 'content') and delta.content else None
                    
                    # If we have content, add it to buffer
                    if content:
                        content_buffer += content
                        word_buffer += content
                        
                        # Check for word boundaries (space, punctuation)
                        if any(char in word_buffer for char in " .,!?;:"):
                            # Split and yield complete words
                            words = word_buffer.split()
                            for word in words[:-1]:  # All but last word
                                yield {
                                    "type": "response",
                                    "content": word + " "
                                }
                            if words:  # Handle last word
                                if word_buffer.strip().endswith(tuple(".,!?;:")):
                                    yield {
                                        "type": "response",
                                        "content": words[-1] + word_buffer[word_buffer.rstrip().rfind(words[-1]) + len(words[-1]):] + " "
                                    }
                                else:
                                    yield {
                                        "type": "response",
                                        "content": words[-1] + " "
                                    }
                            word_buffer = ""
                    
                    # Handle tool calls
                    tool_calls = delta.tool_calls if hasattr(delta, 'tool_calls') and delta.tool_calls else None
                    if tool_calls:
                        for tool_call in tool_calls:
                            yield {
                                "type": "tool_call",
                                "tool_call": {
                                    "id": tool_call.id,
                                    "type": tool_call.type,
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                    }
                                }
                            }
                
                # Handle any remaining content in word buffer
                if word_buffer.strip():
                    yield {
                        "type": "response",
                        "content": word_buffer.strip() + " "
                    }
                
                # If we got no content at all, yield a default response
                if not content_buffer:
                    yield {
                        "type": "response",
                        "content": "Hello! I'm here to help. What can I assist you with today?"
                    }
            else:
                choice = response.choices[0]
                if hasattr(choice, 'message'):
                    message = choice.message
                    if hasattr(message, 'content') and message.content:
                        yield {
                            "type": "response",
                            "content": message.content
                        }
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        for tool_call in message.tool_calls:
                            yield {
                                "type": "tool_call",
                                "tool_call": {
                                    "id": tool_call.id,
                                    "type": tool_call.type,
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                    }
                                }
                            }
                else:
                    yield {
                        "type": "response",
                        "content": "Hello! I'm here to help. What can I assist you with today?"
                    }
                    
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            yield {
                "type": "error",
                "content": f"Error calling OpenAI API: {str(e)}"
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

    def set_openai_key(self, api_key: str):
        """Set or update the OpenAI API key."""
        self.api_keys["openai"] = api_key
        self.openai_client = AsyncOpenAI(api_key=api_key)
        
    def set_anthropic_key(self, api_key: str):
        """Set or update the Anthropic API key."""
        self.api_keys["anthropic"] = api_key
        self.anthropic_client = AsyncAnthropic(api_key=api_key) 