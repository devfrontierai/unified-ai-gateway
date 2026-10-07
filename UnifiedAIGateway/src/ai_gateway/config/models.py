from typing import Literal, Any
from pydantic import BaseModel, Field

class ProviderConfig(BaseModel):
    type: str
    api_key_env: str | None = None
    api_key: str | None = None
    base_url: str | None = None

class ModelConfig(BaseModel):
    provider: str
    model: str

class RoutingConfig(BaseModel):
    strategy: str
    providers: list[str] = Field(default_factory=list)
    weights: list[float] | None = None

class GatewayAppConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080

class AppConfiguration(BaseModel):
    gateway: GatewayAppConfig = Field(default_factory=GatewayAppConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    models: dict[str, ModelConfig] = Field(default_factory=dict)
    routing: dict[str, RoutingConfig] = Field(default_factory=dict)
