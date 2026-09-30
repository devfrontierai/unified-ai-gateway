import os
from typing import Any

from ai_gateway.providers.base import ModelProvider
from ai_gateway.providers.mock import MockProvider
from ai_gateway.providers.openai import OpenAIProvider
from ai_gateway.providers.anthropic import AnthropicProvider
from ai_gateway.providers.gemini import GeminiProvider
from ai_gateway.config.models import AppConfiguration

class ProviderRegistry:
    """Manages the lifecycle and retrieval of configured model providers."""
    
    def __init__(self):
        self._providers: dict[str, ModelProvider] = {}

    def register(self, name: str, provider: ModelProvider):
        self._providers[name] = provider

    def get(self, name: str) -> ModelProvider | None:
        return self._providers.get(name)

    def get_all(self) -> dict[str, ModelProvider]:
        return self._providers

    async def close_all(self):
        for provider in self._providers.values():
            if hasattr(provider, "close"):
                await provider.close()

def build_provider_registry(config: AppConfiguration) -> ProviderRegistry:
    registry = ProviderRegistry()
    
    for name, p_config in config.providers.items():
        api_key = p_config.api_key
        if not api_key and p_config.api_key_env:
            api_key = os.environ.get(p_config.api_key_env)
            
        if p_config.type == "mock":
            registry.register(name, MockProvider())
        elif p_config.type == "openai":
            if not api_key:
                raise ValueError(f"Missing API key for OpenAI provider '{name}'")
            kwargs = {"api_key": api_key}
            if p_config.base_url:
                kwargs["base_url"] = p_config.base_url
            registry.register(name, OpenAIProvider(**kwargs))
        elif p_config.type == "anthropic":
            if not api_key:
                raise ValueError(f"Missing API key for Anthropic provider '{name}'")
            kwargs = {"api_key": api_key}
            if p_config.base_url:
                kwargs["base_url"] = p_config.base_url
            registry.register(name, AnthropicProvider(**kwargs))
        elif p_config.type == "gemini":
            if not api_key:
                raise ValueError(f"Missing API key for Gemini provider '{name}'")
            kwargs = {"api_key": api_key}
            if p_config.base_url:
                kwargs["base_url"] = p_config.base_url
            registry.register(name, GeminiProvider(**kwargs))
        else:
            raise ValueError(f"Unknown provider type: {p_config.type}")
            
    return registry
