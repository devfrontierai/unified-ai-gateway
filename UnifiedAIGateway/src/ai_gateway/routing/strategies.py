import random
from ai_gateway.core.request import ChatRequest
from ai_gateway.routing.base import RoutingStrategy, ModelEndpoint

class StaticStrategy(RoutingStrategy):
    """Always routes to the first available endpoint."""
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates:
            raise ValueError("No candidates available for routing")
        return candidates[0]

class RoundRobinStrategy(RoutingStrategy):
    """Routes to endpoints in a round-robin fashion."""
    def __init__(self):
        self._index = 0

    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates:
            raise ValueError("No candidates available for routing")
        selected = candidates[self._index % len(candidates)]
        self._index += 1
        return selected

class WeightedStrategy(RoutingStrategy):
    """Routes requests based on predefined weights."""
    def __init__(self, weights: list[float]):
        self.weights = weights
        
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates:
            raise ValueError("No candidates available for routing")
        if len(self.weights) != len(candidates):
            # Fallback to static if weights are misconfigured
            return candidates[0]
            
        return random.choices(candidates, weights=self.weights, k=1)[0]

class FallbackStrategy(RoutingStrategy):
    """
    Returns the first endpoint. The actual fallback execution (retrying on failure) 
    is handled by the core execution engine, not the selection logic.
    For selection, we simply return the primary candidate and let the pipeline 
    know about the backups. For now, we return candidates[0].
    """
    async def select(self, request: ChatRequest, candidates: list[ModelEndpoint]) -> ModelEndpoint:
        if not candidates:
            raise ValueError("No candidates available for routing")
        return candidates[0]
