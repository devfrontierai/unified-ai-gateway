import os
import yaml
from ai_gateway.config.models import AppConfiguration

def load_yaml_config(file_path: str) -> AppConfiguration:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        
    return AppConfiguration.model_validate(data)
