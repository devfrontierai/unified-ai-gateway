from contextlib import asynccontextmanager
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
