from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class GatewaySettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080
    config_file: str | None = None

    model_config = SettingsConfigDict(env_prefix="GATEWAY_")

def load_settings() -> GatewaySettings:
    """Load base gateway settings."""
    return GatewaySettings()

# Note: The dynamic YAML configuration for models, routing, and providers 
# will be loaded separately as it has a complex nested structure.
