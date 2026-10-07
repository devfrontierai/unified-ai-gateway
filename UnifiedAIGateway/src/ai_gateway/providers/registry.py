import os
from typing import Any
from ai_gateway.providers.base import ModelProvider
from ai_gateway.providers.mock import MockProvider
# We would import OpenAI, Anthropic, Gemini here

class ProviderRegistry:
    def __init__(self): self._providers = {}
    def register(self, name: str, provider: ModelProvider): self._providers[name] = provider
    def get(self, name: str) -> ModelProvider | None: return self._providers.get(name)
    def get_all(self) -> dict[str, ModelProvider]: return self._providers
    async def close_all(self):
        for provider in self._providers.values():
            if hasattr(provider, "close"): await provider.close()

def build_provider_registry(config) -> ProviderRegistry:
    registry = ProviderRegistry()
    for name, p_config in config.providers.items():
        if p_config.type == "mock": registry.register(name, MockProvider())
        # Actual providers omitted for brevity to speed up examples since mock is enough to test routing/plugins
    return registry
