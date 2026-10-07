from pydantic import BaseModel
class ModelCapabilities(BaseModel):
    streaming: bool = False
    tools: bool = False
    structured_output: bool = False
    embeddings: bool = False
    vision: bool = False
