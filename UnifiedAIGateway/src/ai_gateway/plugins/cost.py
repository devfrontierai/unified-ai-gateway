import structlog
from ai_gateway.plugins.base import GatewayPlugin
from ai_gateway.core.context import GatewayContext

logger = structlog.get_logger(__name__)

class CostPlugin(GatewayPlugin):
    """
    Plugin to capture and calculate estimated costs of provider calls.
    In a real implementation, this would look up pricing from a database or config.
    """
    
    # Mock pricing table (cost per 1k tokens)
    PRICING = {
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "claude-3-5-sonnet-20240620": {"prompt": 0.003, "completion": 0.015},
        "gemini-1.5-pro": {"prompt": 0.0035, "completion": 0.0105},
        "mock-gpt-4o": {"prompt": 0.001, "completion": 0.002},
        "mock-claude-3-5": {"prompt": 0.001, "completion": 0.002}
    }

    async def after_provider_call(self, context: GatewayContext):
        if not context.response or not context.response.usage:
            return
            
        usage = context.response.usage
        model_name = context.selected_endpoint.provider_model if context.selected_endpoint else context.request.model
        
        rates = self.PRICING.get(model_name, {"prompt": 0.0, "completion": 0.0})
        
        prompt_cost = (usage.prompt_tokens / 1000.0) * rates["prompt"]
        completion_cost = (usage.completion_tokens / 1000.0) * rates["completion"]
        total_cost = prompt_cost + completion_cost
        
        context.state["estimated_cost"] = total_cost
        
        logger.info("Cost estimated", 
                    model=model_name, 
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    estimated_cost=total_cost)
