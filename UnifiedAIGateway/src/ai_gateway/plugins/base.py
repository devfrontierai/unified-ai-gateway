from abc import ABC

from ai_gateway.core.context import GatewayContext

class GatewayPlugin(ABC):
    """Base class for all AI Gateway plugins."""
    
    @property
    def name(self) -> str:
        return self.__class__.__name__

    async def before_request(self, context: GatewayContext):
        """Called before any processing or routing happens."""
        pass

    async def before_routing(self, context: GatewayContext):
        """Called before the routing engine selects an endpoint."""
        pass

    async def before_provider_call(self, context: GatewayContext):
        """Called after routing, right before the provider is invoked."""
        pass

    async def after_provider_call(self, context: GatewayContext):
        """Called immediately after a successful provider response."""
        pass

    async def before_response(self, context: GatewayContext):
        """Called right before the response is sent back to the client."""
        pass

    async def on_error(self, context: GatewayContext, error: Exception):
        """Called when an error occurs during the request lifecycle."""
        pass
