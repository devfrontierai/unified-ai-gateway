import structlog
from ai_gateway.plugins.base import GatewayPlugin
from ai_gateway.core.context import GatewayContext

logger = structlog.get_logger(__name__)

class PluginManager:
    """Manages the execution of plugin hooks."""
    
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
                # Plugins shouldn't crash the gateway by default, unless configured to do so (like a hard governance policy).
                # For Phase 9, we log and continue. Governance plugin will raise explicit exceptions that we'll handle gracefully.
                logger.error(f"Plugin {plugin.name} failed during {hook_name}: {e}")
                
                # If it's a specific gateway error (e.g., PolicyDeniedError), we re-raise it
                if type(e).__name__ in ("PolicyDeniedError", "SecurityViolationError"):
                    raise
