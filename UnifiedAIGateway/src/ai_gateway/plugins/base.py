from abc import ABC
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
