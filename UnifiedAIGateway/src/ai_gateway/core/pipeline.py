import asyncio
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
        """Executes a provider call with exponential backoff for safe retries."""
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                if is_chat:
                    if is_stream:
                        # For streaming, we don't retry once the stream starts successfully.
                        # Retrying a broken stream requires client-side coordination.
                        return provider.stream_chat_completion(request)
                    else:
                        return await provider.chat_completion(request)
                else:
                    return await provider.embeddings(request)
            except Exception as e:
                # Classify error to see if it's retryable (e.g., 429 Rate Limit, 503 Unavailable)
                # In a real implementation, we would inspect the HTTP status code from httpx.HTTPStatusError
                is_retryable = isinstance(e, (ProviderRateLimitError, ProviderUnavailableError, ProviderTimeoutError))
                # For this prototype, we'll assume httpx errors might be retryable if they are connect timeouts etc.
                import httpx
                if isinstance(e, httpx.HTTPError) or is_retryable:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Provider call failed. Retrying in {delay}s (attempt {attempt + 1}/{max_retries})", error=str(e))
                        await asyncio.sleep(delay)
                        continue
                
                # If we get here, it's not retryable or we exhausted retries
                raise ProviderUnavailableError(f"Provider call failed: {e}") from e

    async def execute_chat(self, context: GatewayContext) -> ChatResponse | AsyncGenerator[ChatChunk, None]:
        await self.plugin_manager.execute_hook("before_request", context)
        
        try:
            await self.plugin_manager.execute_hook("before_routing", context)
            endpoint = await self.routing_engine.route(context.request)
            context.selected_endpoint = endpoint
            
            await self.plugin_manager.execute_hook("before_provider_call", context)
            
            # Execute with retry logic
            result = await self._execute_with_retry(
                provider=endpoint.provider, 
                request=context.request, 
                is_chat=True, 
                is_stream=context.request.stream
            )
            
            if context.request.stream:
                # Wrap the generator to execute post-hooks when stream finishes
                async def wrapped_stream():
                    try:
                        async for chunk in result:
                            yield chunk
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
            
            result = await self._execute_with_retry(
                provider=endpoint.provider, 
                request=context.request, 
                is_chat=False, 
                is_stream=False
            )
            
            context.response = result
            await self.plugin_manager.execute_hook("after_provider_call", context)
            await self.plugin_manager.execute_hook("before_response", context)
            return context.response
            
        except Exception as e:
            context.error = e
            await self.plugin_manager.execute_hook("on_error", context, error=e)
            raise
