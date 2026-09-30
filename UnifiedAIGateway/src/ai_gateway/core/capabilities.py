from pydantic import BaseModel

class ModelCapabilities(BaseModel):
    """Represents the capabilities supported by a specific model."""
    streaming: bool = False
    tools: bool = False
    structured_output: bool = False
    embeddings: bool = False
    vision: bool = False
