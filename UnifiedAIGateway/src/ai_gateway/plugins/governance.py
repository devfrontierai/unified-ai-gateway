import structlog
from ai_gateway.plugins.base import GatewayPlugin
from ai_gateway.core.context import GatewayContext
from ai_gateway.core.errors import PolicyDeniedError

logger = structlog.get_logger(__name__)

class GovernancePlugin(GatewayPlugin):
    """
    Basic Governance plugin to intercept requests and evaluate policies.
    """
    
    async def before_routing(self, context: GatewayContext):
        # Example policy: Deny requests with missing user_id for specific tenants
        if context.tenant_id == "strict-tenant" and not context.user_id:
            raise PolicyDeniedError("Policy Violation: user_id is required for strict-tenant")
            
        # Example policy: Keyword blocking (Very basic DLP)
        if hasattr(context.request, "messages"):
            for msg in context.request.messages:
                content = msg.content
                if isinstance(content, str) and "TOP_SECRET_PROJECT_X" in content:
                    logger.warning("Blocked request containing restricted keyword", request_id=context.request_id)
                    raise PolicyDeniedError("Policy Violation: Prompt contains restricted keywords")
