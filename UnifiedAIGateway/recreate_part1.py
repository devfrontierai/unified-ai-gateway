import os

files = {
    "pyproject.toml": """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "ai-gateway"
version = "0.1.0"
description = "Provider-Neutral Enterprise AI Gateway"
authors = [{name = "AI Architect"}]
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.29.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.1",
    "httpx>=0.27.0",
    "structlog>=24.1.0",
    "pyyaml>=6.0.1",
]

[project.optional-dependencies]
dev = ["pytest>=8.1.1", "pytest-asyncio>=0.23.6", "mypy>=1.9.0", "ruff>=0.3.5"]

[project.scripts]
ai-gateway = "ai_gateway.server.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
""",

    "src/ai_gateway/core/capabilities.py": """from pydantic import BaseModel
class ModelCapabilities(BaseModel):
    streaming: bool = False
    tools: bool = False
    structured_output: bool = False
    embeddings: bool = False
    vision: bool = False
""",

    "src/ai_gateway/core/request.py": """from typing import Any, Literal
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None

class ToolDefinition(BaseModel):
    type: Literal["function"]
    function: dict[str, Any]

class ChatRequest(BaseModel):
    request_id: str
    tenant_id: str
    application_id: str | None = None
    agent_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    model: str
    messages: list[Message]
    temperature: float | None = None
    max_tokens: int | None = None
    tools: list[ToolDefinition] | None = None
    tool_choice: Any | None = None
    stream: bool = False
    response_format: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class EmbeddingRequest(BaseModel):
    request_id: str
    tenant_id: str
    application_id: str | None = None
    agent_id: str | None = None
    user_id: str | None = None
    model: str
    input: str | list[str]
    dimensions: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
""",

    "src/ai_gateway/core/response.py": """from typing import Any
from pydantic import BaseModel

class ChatUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatChoice(BaseModel):
    index: int
    message: dict[str, Any]
    finish_reason: str | None = None

class ChatResponse(BaseModel):
    id: str
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage | None = None
    created: int
    metadata: dict[str, Any] = {}

class ChatChunkChoice(BaseModel):
    index: int
    delta: dict[str, Any]
    finish_reason: str | None = None

class ChatChunk(BaseModel):
    id: str
    model: str
    choices: list[ChatChunkChoice]
    created: int
    usage: ChatUsage | None = None

class EmbeddingData(BaseModel):
    object: str = "embedding"
    index: int
    embedding: list[float]

class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[EmbeddingData]
    model: str
    usage: ChatUsage | None = None
""",

    "src/ai_gateway/core/errors.py": """class GatewayError(Exception): pass
class AuthenticationError(GatewayError): pass
class AuthorizationError(GatewayError): pass
class ModelNotFoundError(GatewayError): pass
class ProviderUnavailableError(GatewayError): pass
class ProviderTimeoutError(GatewayError): pass
class ProviderRateLimitError(GatewayError): pass
class UnsupportedCapabilityError(GatewayError): pass
class RoutingError(GatewayError): pass
class PolicyDeniedError(GatewayError): pass
class GatewayConfigurationError(GatewayError): pass
class SecurityViolationError(GatewayError): pass
""",

    "src/ai_gateway/core/context.py": """from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field
from ai_gateway.core.request import ChatRequest, EmbeddingRequest
from ai_gateway.core.response import ChatResponse, EmbeddingResponse

class GatewayContext(BaseModel):
    request_id: str
    tenant_id: str
    application_id: str | None = None
    user_id: str | None = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    request: ChatRequest | EmbeddingRequest | None = None
    selected_endpoint: Any | None = None
    response: ChatResponse | EmbeddingResponse | None = None
    state: dict[str, Any] = Field(default_factory=dict)
    error: Exception | None = None
    
    class Config:
        arbitrary_types_allowed = True
""",

    "src/ai_gateway/plugins/base.py": """from abc import ABC
from ai_gateway.core.context import GatewayContext

class GatewayPlugin(ABC):
    @property
    def name(self) -> str:
        return self.__class__.__name__

    async def before_request(self, context: GatewayContext): pass
    async def before_routing(self, context: GatewayContext): pass
    async def before_provider_call(self, context: GatewayContext): pass
    async def after_provider_call(self, context: GatewayContext): pass
    async def before_response(self, context: GatewayContext): pass
    async def on_error(self, context: GatewayContext, error: Exception): pass
""",

    "src/ai_gateway/plugins/manager.py": """import structlog
from ai_gateway.plugins.base import GatewayPlugin
from ai_gateway.core.context import GatewayContext

logger = structlog.get_logger(__name__)

class PluginManager:
    def __init__(self):
        self._plugins: list[GatewayPlugin] = []

    def register(self, plugin: GatewayPlugin):
        self._plugins.append(plugin)

    async def execute_hook(self, hook_name: str, context: GatewayContext, **kwargs):
        for plugin in self._plugins:
            try:
                method = getattr(plugin, hook_name, None)
                if method:
                    if kwargs:
                        await method(context, **kwargs)
                    else:
                        await method(context)
            except Exception as e:
                logger.error(f"Plugin {plugin.name} failed during {hook_name}: {e}")
                if type(e).__name__ in ("PolicyDeniedError", "SecurityViolationError"):
                    raise
""",

    "src/ai_gateway/events/models.py": """from datetime import datetime
from pydantic import BaseModel, Field

class BaseEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str
    tenant_id: str
    application_id: str | None = None
    agent_id: str | None = None
    user_id: str | None = None

class ModelCallEvent(BaseEvent):
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: float
    status: str
    estimated_cost: float | None = None
    error_message: str | None = None
""",

    "src/ai_gateway/events/sink.py": """from abc import ABC, abstractmethod
import structlog
from ai_gateway.events.models import BaseEvent

logger = structlog.get_logger(__name__)

class EventSink(ABC):
    @abstractmethod
    async def publish(self, event: BaseEvent): pass

class InMemorySink(EventSink):
    def __init__(self):
        self.events: list[BaseEvent] = []
    async def publish(self, event: BaseEvent):
        self.events.append(event)

class StructuredLogSink(EventSink):
    async def publish(self, event: BaseEvent):
        logger.info("gateway_event", event_type=event.__class__.__name__, **event.model_dump())
""",

    "src/ai_gateway/routing/base.py": """from abc import ABC, abstractmethod
from pydantic import BaseModel
from ai_gateway.core.request import ChatRequest

class ModelEndpoint(BaseModel):
    provider_name: str
    provider: Any
    provider_model: str
    class Config:
        arbitrary_types_allowed = True

class RoutingStrategy(ABC):
    @abstractmethod
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        ...
""",

    "src/ai_gateway/routing/strategies.py": """import random
from ai_gateway.core.request import ChatRequest
from ai_gateway.routing.base import RoutingStrategy, ModelEndpoint

class StaticStrategy(RoutingStrategy):
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates: raise ValueError("No candidates")
        return candidates[0]

class RoundRobinStrategy(RoutingStrategy):
    def __init__(self):
        self._index = 0
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates: raise ValueError("No candidates")
        selected = candidates[self._index % len(candidates)]
        self._index += 1
        return selected

class WeightedStrategy(RoutingStrategy):
    def __init__(self, weights: list[float]):
        self.weights = weights
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates: raise ValueError("No candidates")
        if len(self.weights) != len(candidates): return candidates[0]
        return random.choices(candidates, weights=self.weights, k=1)[0]

class FallbackStrategy(RoutingStrategy):
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates: raise ValueError("No candidates")
        return candidates[0]
""",

    "src/ai_gateway/routing/engine.py": """from ai_gateway.core.request import ChatRequest
from ai_gateway.routing.base import ModelEndpoint, RoutingStrategy
from ai_gateway.routing.strategies import StaticStrategy, RoundRobinStrategy, WeightedStrategy, FallbackStrategy

class RoutingEngine:
    def __init__(self, config, registry):
        self.config = config
        self.registry = registry
        self.strategies = {}
        self._initialize_strategies()

    def _initialize_strategies(self):
        for route_name, route_config in self.config.routing.items():
            if route_config.strategy == "static": self.strategies[route_name] = StaticStrategy()
            elif route_config.strategy == "round_robin": self.strategies[route_name] = RoundRobinStrategy()
            elif route_config.strategy == "weighted": self.strategies[route_name] = WeightedStrategy(route_config.weights or [1.0]*len(route_config.providers))
            elif route_config.strategy == "fallback": self.strategies[route_name] = FallbackStrategy()
            else: self.strategies[route_name] = StaticStrategy()

    def get_candidates(self, alias: str) -> list[ModelEndpoint]:
        candidates = []
        if alias in self.config.routing:
            route_config = self.config.routing[alias]
            for provider_name in route_config.providers:
                provider = self.registry.get(provider_name)
                provider_model = alias
                for m_alias, m_config in self.config.models.items():
                    if m_config.provider == provider_name and (m_alias == alias or m_alias.startswith(alias)):
                        provider_model = m_config.model
                        break
                if provider:
                    candidates.append(ModelEndpoint(provider_name=provider_name, provider=provider, provider_model=provider_model))
        elif alias in self.config.models:
            model_config = self.config.models[alias]
            provider = self.registry.get(model_config.provider)
            if provider:
                candidates.append(ModelEndpoint(provider_name=model_config.provider, provider=provider, provider_model=model_config.model))
        return candidates

    async def route(self, request: ChatRequest) -> ModelEndpoint:
        candidates = self.get_candidates(request.model)
        if not candidates: raise ValueError(f"No configured routing for alias: {request.model}")
        strategy = self.strategies.get(request.model, StaticStrategy())
        selected = await strategy.select(request, candidates)
        request.model = selected.provider_model
        return selected
""",

    "src/ai_gateway/core/pipeline.py": """import asyncio
import structlog
from typing import AsyncGenerator
from ai_gateway.core.request import ChatRequest, EmbeddingRequest
from ai_gateway.core.context import GatewayContext
from ai_gateway.core.response import ChatResponse, ChatChunk
from ai_gateway.routing.engine import RoutingEngine
from ai_gateway.plugins.manager import PluginManager
from ai_gateway.core.errors import ProviderRateLimitError, ProviderUnavailableError, ProviderTimeoutError

logger = structlog.get_logger(__name__)

class ExecutionPipeline:
    def __init__(self, routing_engine: RoutingEngine, plugin_manager: PluginManager):
        self.routing_engine = routing_engine
        self.plugin_manager = plugin_manager

    async def _execute_with_retry(self, provider, request: ChatRequest | EmbeddingRequest, is_chat: bool, is_stream: bool):
        max_retries = 3
        base_delay = 1.0
        for attempt in range(max_retries):
            try:
                if is_chat:
                    if is_stream: return provider.stream_chat_completion(request)
                    else: return await provider.chat_completion(request)
                else:
                    return await provider.embeddings(request)
            except Exception as e:
                import httpx
                is_retryable = isinstance(e, (ProviderRateLimitError, ProviderUnavailableError, ProviderTimeoutError))
                if isinstance(e, httpx.HTTPError) or is_retryable:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Provider call failed. Retrying in {delay}s (attempt {attempt + 1}/{max_retries})", error=str(e))
                        await asyncio.sleep(delay)
                        continue
                raise ProviderUnavailableError(f"Provider call failed: {e}") from e

    async def execute_chat(self, context: GatewayContext) -> ChatResponse | AsyncGenerator[ChatChunk, None]:
        await self.plugin_manager.execute_hook("before_request", context)
        try:
            await self.plugin_manager.execute_hook("before_routing", context)
            endpoint = await self.routing_engine.route(context.request)
            context.selected_endpoint = endpoint
            await self.plugin_manager.execute_hook("before_provider_call", context)
            
            result = await self._execute_with_retry(endpoint.provider, context.request, True, context.request.stream)
            
            if context.request.stream:
                async def wrapped_stream():
                    try:
                        async for chunk in result: yield chunk
                        await self.plugin_manager.execute_hook("after_provider_call", context)
                        await self.plugin_manager.execute_hook("before_response", context)
                    except Exception as e:
                        context.error = e
                        await self.plugin_manager.execute_hook("on_error", context, error=e)
                        raise
                return wrapped_stream()
            else:
                context.response = result
                await self.plugin_manager.execute_hook("after_provider_call", context)
                await self.plugin_manager.execute_hook("before_response", context)
                return context.response
        except Exception as e:
            context.error = e
            await self.plugin_manager.execute_hook("on_error", context, error=e)
            raise

    async def execute_embeddings(self, context: GatewayContext):
        await self.plugin_manager.execute_hook("before_request", context)
        try:
            await self.plugin_manager.execute_hook("before_routing", context)
            endpoint = await self.routing_engine.route(context.request)
            context.selected_endpoint = endpoint
            await self.plugin_manager.execute_hook("before_provider_call", context)
            
            result = await self._execute_with_retry(endpoint.provider, context.request, False, False)
            
            context.response = result
            await self.plugin_manager.execute_hook("after_provider_call", context)
            await self.plugin_manager.execute_hook("before_response", context)
            return context.response
        except Exception as e:
            context.error = e
            await self.plugin_manager.execute_hook("on_error", context, error=e)
            raise
"""
}

# Write files
for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Core files recreated successfully!")
