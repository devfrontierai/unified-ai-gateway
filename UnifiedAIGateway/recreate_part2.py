import os

files = {
    "src/ai_gateway/providers/base.py": """from abc import ABC, abstractmethod
from typing import AsyncIterator, Any
from pydantic import BaseModel
from ai_gateway.core.request import ChatRequest, EmbeddingRequest
from ai_gateway.core.response import ChatResponse, ChatChunk, EmbeddingResponse
from ai_gateway.core.capabilities import ModelCapabilities

class ModelInfo(BaseModel):
    id: str
    capabilities: ModelCapabilities

class ProviderHealth(BaseModel):
    status: str
    details: dict[str, Any] = {}

class ModelProvider(ABC):
    @abstractmethod
    async def chat_completion(self, request: ChatRequest) -> ChatResponse: ...
    @abstractmethod
    async def stream_chat_completion(self, request: ChatRequest) -> AsyncIterator[ChatChunk]: ...
    @abstractmethod
    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse: ...
    @abstractmethod
    async def list_models(self) -> list[ModelInfo]: ...
    @abstractmethod
    async def health(self) -> ProviderHealth: ...
""",

    "src/ai_gateway/providers/mock.py": """from typing import AsyncIterator, Any
import time, asyncio, uuid
from ai_gateway.core.request import ChatRequest, EmbeddingRequest
from ai_gateway.core.response import ChatResponse, ChatChunk, EmbeddingResponse, ChatChoice, ChatChunkChoice, ChatUsage, EmbeddingData
from ai_gateway.core.capabilities import ModelCapabilities
from ai_gateway.providers.base import ModelProvider, ModelInfo, ProviderHealth

class MockProvider(ModelProvider):
    def __init__(self, latency: float = 0.1): self.latency = latency
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        await asyncio.sleep(self.latency)
        return ChatResponse(id=f"chatcmpl-{uuid.uuid4().hex[:12]}", model=request.model, created=int(time.time()), choices=[ChatChoice(index=0, message={"role": "assistant", "content": f"Mock response to: {request.messages[-1].content}"}, finish_reason="stop")], usage=ChatUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30))
    async def stream_chat_completion(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        resp_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())
        words = f"Mock response to: {request.messages[-1].content}".split()
        for i, word in enumerate(words):
            await asyncio.sleep(self.latency / len(words))
            yield ChatChunk(id=resp_id, model=request.model, created=created, choices=[ChatChunkChoice(index=0, delta={"role": "assistant", "content": word + " " if i > 0 else word}, finish_reason=None if i < len(words) - 1 else "stop")])
    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        await asyncio.sleep(self.latency)
        input_texts = request.input if isinstance(request.input, list) else [request.input]
        return EmbeddingResponse(model=request.model, data=[EmbeddingData(index=i, embedding=[0.1, 0.2, 0.3]) for i, _ in enumerate(input_texts)], usage=ChatUsage(prompt_tokens=10, completion_tokens=0, total_tokens=10))
    async def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(id="mock-model", capabilities=ModelCapabilities(streaming=True, embeddings=True))]
    async def health(self) -> ProviderHealth: return ProviderHealth(status="ok")
""",

    "src/ai_gateway/providers/registry.py": """import os
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
""",

    "src/ai_gateway/config/settings.py": """from pydantic_settings import BaseSettings, SettingsConfigDict
class GatewaySettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080
    config_file: str | None = None
    model_config = SettingsConfigDict(env_prefix="GATEWAY_")
def load_settings() -> GatewaySettings: return GatewaySettings()
""",

    "src/ai_gateway/config/models.py": """from typing import Literal, Any
from pydantic import BaseModel, Field

class ProviderConfig(BaseModel):
    type: str
    api_key_env: str | None = None
    api_key: str | None = None
    base_url: str | None = None

class ModelConfig(BaseModel):
    provider: str
    model: str

class RoutingConfig(BaseModel):
    strategy: str
    providers: list[str] = Field(default_factory=list)
    weights: list[float] | None = None

class GatewayAppConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080

class AppConfiguration(BaseModel):
    gateway: GatewayAppConfig = Field(default_factory=GatewayAppConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    models: dict[str, ModelConfig] = Field(default_factory=dict)
    routing: dict[str, RoutingConfig] = Field(default_factory=dict)
""",

    "src/ai_gateway/config/loader.py": """import os, yaml
from ai_gateway.config.models import AppConfiguration

def load_yaml_config(file_path: str) -> AppConfiguration:
    if not os.path.exists(file_path): raise FileNotFoundError(f"Config not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f: data = yaml.safe_load(f) or {}
    return AppConfiguration.model_validate(data)
""",

    "src/ai_gateway/api/openai/models.py": """from typing import Any, Literal
from pydantic import BaseModel

class OpenAIMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]] | None = None
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None

class OpenAIChatRequest(BaseModel):
    model: str
    messages: list[OpenAIMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False
    tools: list[dict[str, Any]] | None = None
    tool_choice: Any | None = None
    response_format: dict[str, Any] | None = None
    user: str | None = None

class OpenAIEmbeddingRequest(BaseModel):
    model: str
    input: str | list[str]
    dimensions: int | None = None
    user: str | None = None
""",

    "src/ai_gateway/api/openai/routes.py": """from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import uuid
from typing import AsyncGenerator

from ai_gateway.api.openai.models import OpenAIChatRequest, OpenAIEmbeddingRequest
from ai_gateway.core.request import ChatRequest, Message, EmbeddingRequest
from ai_gateway.core.pipeline import ExecutionPipeline
from ai_gateway.core.context import GatewayContext
from ai_gateway.core.response import ChatChunk

router = APIRouter()

def convert_chat_request(req: OpenAIChatRequest, request_id: str) -> ChatRequest:
    messages = [Message(role=m.role, content=m.content, name=m.name, tool_calls=m.tool_calls, tool_call_id=m.tool_call_id) for m in req.messages]
    return ChatRequest(request_id=request_id, tenant_id="default-tenant", user_id=req.user, model=req.model, messages=messages, temperature=req.temperature, max_tokens=req.max_tokens, stream=req.stream, response_format=req.response_format)

async def stream_generator(generator) -> AsyncGenerator[str, None]:
    async for chunk in generator:
        if isinstance(chunk, ChatChunk): yield f"data: {chunk.model_dump_json(exclude_none=True)}\\n\\n"
    yield "data: [DONE]\\n\\n"

@router.post("/chat/completions")
async def chat_completions(req: Request, request: OpenAIChatRequest):
    req_id = f"req-{uuid.uuid4().hex}"
    internal_req = convert_chat_request(request, req_id)
    pipeline: ExecutionPipeline = req.app.state.pipeline
    context = GatewayContext(request_id=req_id, tenant_id="default-tenant", user_id=request.user, request=internal_req)
    try:
        result = await pipeline.execute_chat(context)
        if request.stream: return StreamingResponse(stream_generator(result), media_type="text/event-stream")
        else: return result.model_dump(exclude_none=True)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/embeddings")
async def embeddings(req: Request, request: OpenAIEmbeddingRequest):
    req_id = f"req-{uuid.uuid4().hex}"
    internal_req = EmbeddingRequest(request_id=req_id, tenant_id="default-tenant", user_id=request.user, model=request.model, input=request.input, dimensions=request.dimensions)
    pipeline: ExecutionPipeline = req.app.state.pipeline
    context = GatewayContext(request_id=req_id, tenant_id="default-tenant", user_id=request.user, request=internal_req)
    try:
        result = await pipeline.execute_embeddings(context)
        return result.model_dump(exclude_none=True)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models(req: Request):
    config = req.app.state.gateway_config
    models = list(set(list(config.models.keys()) + list(config.routing.keys())))
    return {"object": "list", "data": [{"id": m, "object": "model", "created": 1677610602, "owned_by": "ai-gateway"} for m in models]}
""",

    "src/ai_gateway/server/app.py": """from contextlib import asynccontextmanager
from fastapi import FastAPI
import os, structlog
from ai_gateway.api.openai.routes import router as openai_router
from ai_gateway.config.loader import load_yaml_config
from ai_gateway.providers.registry import build_provider_registry
from ai_gateway.routing.engine import RoutingEngine
from ai_gateway.config.settings import load_settings
from ai_gateway.plugins.manager import PluginManager
from ai_gateway.core.pipeline import ExecutionPipeline
from ai_gateway.events.sink import StructuredLogSink
from ai_gateway.plugins.cost import CostPlugin
from ai_gateway.plugins.audit import AuditPlugin
from ai_gateway.plugins.governance import GovernancePlugin

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    config_path = settings.config_file or os.environ.get("GATEWAY_CONFIG_FILE", "config.yaml")
    config = load_yaml_config(config_path)
    registry = build_provider_registry(config)
    routing_engine = RoutingEngine(config, registry)
    plugin_manager = PluginManager()
    event_sink = StructuredLogSink()
    app.state.event_sink = event_sink
    
    plugin_manager.register(GovernancePlugin())
    plugin_manager.register(CostPlugin())
    plugin_manager.register(AuditPlugin(event_sink))
    
    pipeline = ExecutionPipeline(routing_engine, plugin_manager)
    
    app.state.gateway_config = config
    app.state.provider_registry = registry
    app.state.routing_engine = routing_engine
    app.state.plugin_manager = plugin_manager
    app.state.pipeline = pipeline
    
    logger.info("AI Gateway started")
    yield
    await registry.close_all()

def create_app() -> FastAPI:
    app = FastAPI(title="AI Gateway", version="0.1.0", lifespan=lifespan)
    @app.get("/health")
    async def health_check(): return {"status": "ok"}
    app.include_router(openai_router, prefix="/v1", tags=["OpenAI Compatible"])
    return app

app = create_app()
""",

    "src/ai_gateway/server/cli.py": """import argparse, uvicorn
from ai_gateway.config.settings import load_settings

def start_server(config_file: str | None = None):
    settings = load_settings()
    if config_file: settings.config_file = config_file
    uvicorn.run("ai_gateway.server.app:app", host=settings.host, port=settings.port, reload=False)

def main():
    parser = argparse.ArgumentParser(description="AI Gateway CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--config", type=str, default=None)
    args = parser.parse_args()
    if args.command == "start": start_server(args.config)

if __name__ == "__main__": main()
"""
}

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Part 2 files recreated successfully!")
