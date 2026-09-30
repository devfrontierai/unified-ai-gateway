from typing import Literal, Any
from pydantic import BaseModel, Field

class ProviderConfig(BaseModel):
    type: Literal["openai", "anthropic", "gemini", "mock"]
    api_key_env: str | None = None
    api_key: str | None = None
    base_url: str | None = None

class ModelConfig(BaseModel):
    provider: str
    model: str

class RoutingConfig(BaseModel):
    strategy: Literal["static", "fallback", "weighted", "round_robin"]
    providers: list[str] = Field(default_factory=list)
    weights: list[float] | None = None  # for weighted routing

class GatewayAppConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    activity_monitor: bool = False
    cost_monitor: bool = False
    control_policies: bool = False

class AppConfiguration(BaseModel):
    """The root configuration object loaded from YAML."""
    gateway: GatewayAppConfig = Field(default_factory=GatewayAppConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    models: dict[str, ModelConfig] = Field(default_factory=dict)
    routing: dict[str, RoutingConfig] = Field(default_factory=dict)
