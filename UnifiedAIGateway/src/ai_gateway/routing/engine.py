from ai_gateway.core.request import ChatRequest
from ai_gateway.routing.base import ModelEndpoint, RoutingStrategy
from ai_gateway.routing.strategies import StaticStrategy, RoundRobinStrategy, WeightedStrategy, FallbackStrategy

class RoutingEngine:
    def __init__(self, config, registry):
        self.config = config
        self.registry = registry
        self.strategies = {}
        self._initialize_strategies()

    def _initialize_strategies(self):
        for route_name, route_config in self.config.routing.items():
            if route_config.strategy == "static": self.strategies[route_name] = StaticStrategy()
            elif route_config.strategy == "round_robin": self.strategies[route_name] = RoundRobinStrategy()
            elif route_config.strategy == "weighted": self.strategies[route_name] = WeightedStrategy(route_config.weights or [1.0]*len(route_config.providers))
            elif route_config.strategy == "fallback": self.strategies[route_name] = FallbackStrategy()
            else: self.strategies[route_name] = StaticStrategy()

    def get_candidates(self, alias: str) -> list[ModelEndpoint]:
        candidates = []
        if alias in self.config.routing:
            route_config = self.config.routing[alias]
            for provider_name in route_config.providers:
                provider = self.registry.get(provider_name)
                provider_model = alias
                for m_alias, m_config in self.config.models.items():
                    if m_config.provider == provider_name and (m_alias == alias or m_alias.startswith(alias)):
                        provider_model = m_config.model
                        break
                if provider:
                    candidates.append(ModelEndpoint(provider_name=provider_name, provider=provider, provider_model=provider_model))
        elif alias in self.config.models:
            model_config = self.config.models[alias]
            provider = self.registry.get(model_config.provider)
            if provider:
                candidates.append(ModelEndpoint(provider_name=model_config.provider, provider=provider, provider_model=model_config.model))
        return candidates

    async def route(self, request: ChatRequest) -> ModelEndpoint:
        candidates = self.get_candidates(request.model)
        if not candidates: raise ValueError(f"No configured routing for alias: {request.model}")
        strategy = self.strategies.get(request.model, StaticStrategy())
        selected = await strategy.select(request, candidates)
        request.model = selected.provider_model
        return selected
