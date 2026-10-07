from datetime import datetime
import structlog
from ai_gateway.plugins.base import GatewayPlugin
from ai_gateway.core.context import GatewayContext
from ai_gateway.events.models import ModelCallEvent
from ai_gateway.events.sink import EventSink

logger = structlog.get_logger(__name__)

class AuditPlugin(GatewayPlugin):
    """
    Plugin to generate normalized audit events for every provider invocation.
    """
    
    def __init__(self, event_sink: EventSink):
        self.event_sink = event_sink

    async def _emit_event(self, context: GatewayContext, status: str):
        end_time = datetime.utcnow()
        latency = (end_time - context.start_time).total_seconds() * 1000.0
        
        usage = getattr(context.response, "usage", None) if context.response else None
        
        event = ModelCallEvent(
            event_id=context.request_id,
            request_id=context.request_id,
            tenant_id=context.tenant_id,
            application_id=context.application_id,
            user_id=context.user_id,
            provider=context.selected_endpoint.provider_name if context.selected_endpoint else "unknown",
            model=context.selected_endpoint.provider_model if context.selected_endpoint else context.request.model,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            latency_ms=latency,
            status=status,
            estimated_cost=context.state.get("estimated_cost"),
            error_message=str(context.error) if context.error else None
        )
        
        await self.event_sink.publish(event)

    async def after_provider_call(self, context: GatewayContext):
        await self._emit_event(context, "success")

    async def on_error(self, context: GatewayContext, error: Exception):
        await self._emit_event(context, "error")
