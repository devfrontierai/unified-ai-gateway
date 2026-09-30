from ai_gateway.core.request import ChatRequest
from ai_gateway.routing.base import ModelEndpoint, RoutingStrategy
from ai_gateway.routing.strategies import StaticStrategy, RoundRobinStrategy, WeightedStrategy, FallbackStrategy
from ai_gateway.config.models import AppConfiguration
from ai_gateway.providers.registry import ProviderRegistry

class RoutingEngine:
    def __init__(self, config: AppConfiguration, registry: ProviderRegistry):
        self.config = config
        self.registry = registry
        
        self.strategies: dict[str, RoutingStrategy] = {}
        self._initialize_strategies()

    def _initialize_strategies(self):
        for route_name, route_config in self.config.routing.items():
            if route_config.strategy == "static":
                self.strategies[route_name] = StaticStrategy()
            elif route_config.strategy == "round_robin":
                self.strategies[route_name] = RoundRobinStrategy()
            elif route_config.strategy == "weighted":
                weights = route_config.weights or [1.0] * len(route_config.providers)
                self.strategies[route_name] = WeightedStrategy(weights)
            elif route_config.strategy == "fallback":
                self.strategies[route_name] = FallbackStrategy()
            else:
                # Default to static
                self.strategies[route_name] = StaticStrategy()

    def get_candidates(self, alias: str) -> list[ModelEndpoint]:
        candidates = []
        
        # Determine which route to use
        route_alias = alias
        if route_alias not in self.config.routing:
            if "*" in self.config.routing:
                route_alias = "*"
            elif len(self.config.routing) == 1:
                route_alias = list(self.config.routing.keys())[0]

        # Is it a routing rule alias?
        if route_alias in self.config.routing:
            route_config = self.config.routing[route_alias]
            for provider_name in route_config.providers:
                provider = self.registry.get(provider_name)
                provider_model = alias # Use requested alias as fallback
                
                # Try to find specific model config for this alias and provider
                for m_alias, m_config in self.config.models.items():
                    if m_config.provider == provider_name and (m_alias == alias or m_alias.startswith(alias)):
                        provider_model = m_config.model
                        break
                        
                if provider:
                    candidates.append(ModelEndpoint(
                        provider_name=provider_name,
                        provider=provider,
                        provider_model=provider_model
                    ))
                    
        # Is it a direct model alias?
        elif alias in self.config.models:
            model_config = self.config.models[alias]
            provider = self.registry.get(model_config.provider)
            if provider:
                candidates.append(ModelEndpoint(
                    provider_name=model_config.provider,
                    provider=provider,
                    provider_model=model_config.model
                ))
                
        return candidates

    async def route(self, request: ChatRequest) -> ModelEndpoint:
        alias = request.model
        candidates = self.get_candidates(alias)
        
        if not candidates:
            raise ValueError(f"No configured routing or models found for alias: {alias}")
            
        route_alias = alias
        if route_alias not in self.strategies:
            if "*" in self.strategies:
                route_alias = "*"
            elif len(self.strategies) == 1:
                route_alias = list(self.strategies.keys())[0]

        # Select strategy
        strategy = self.strategies.get(route_alias, StaticStrategy())
        
        selected_endpoint = await strategy.select(request, candidates)
        
        # Overwrite the request model to the actual provider model
        request.model = selected_endpoint.provider_model
        
        return selected_endpoint
