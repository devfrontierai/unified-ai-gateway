from pydantic_settings import BaseSettings, SettingsConfigDict
class GatewaySettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080
    config_file: str | None = None
    model_config = SettingsConfigDict(env_prefix="GATEWAY_")
def load_settings() -> GatewaySettings: return GatewaySettings()
