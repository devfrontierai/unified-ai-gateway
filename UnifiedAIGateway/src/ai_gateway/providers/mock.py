from typing import AsyncIterator, Any
import time
import asyncio
import uuid

from ai_gateway.core.request import ChatRequest, EmbeddingRequest
from ai_gateway.core.response import (
    ChatResponse, ChatChunk, EmbeddingResponse,
    ChatChoice, ChatChunkChoice, ChatUsage, EmbeddingData
)
from ai_gateway.core.capabilities import ModelCapabilities
from ai_gateway.providers.base import ModelProvider, ModelInfo, ProviderHealth

class MockProvider(ModelProvider):
    """A mock provider for testing and validation."""

    def __init__(self, latency: float = 0.1):
        self.latency = latency

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        await asyncio.sleep(self.latency)
        
        return ChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            model=request.model,
            created=int(time.time()),
            choices=[
                ChatChoice(
                    index=0,
                    message={"role": "assistant", "content": f"Mock response to: {request.messages[-1].content}"},
                    finish_reason="stop"
                )
            ],
            usage=ChatUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        )

    async def stream_chat_completion(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        resp_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())
        words = f"Mock response to: {request.messages[-1].content}".split()
        
        for i, word in enumerate(words):
            await asyncio.sleep(self.latency / len(words))
            yield ChatChunk(
                id=resp_id,
                model=request.model,
                created=created,
                choices=[
                    ChatChunkChoice(
                        index=0,
                        delta={"role": "assistant", "content": word + " " if i > 0 else word},
                        finish_reason=None if i < len(words) - 1 else "stop"
                    )
                ]
            )

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        await asyncio.sleep(self.latency)
        input_texts = request.input if isinstance(request.input, list) else [request.input]
        
        data = []
        for i, _ in enumerate(input_texts):
            data.append(EmbeddingData(index=i, embedding=[0.1, 0.2, 0.3]))
            
        return EmbeddingResponse(
            model=request.model,
            data=data,
            usage=ChatUsage(prompt_tokens=10, completion_tokens=0, total_tokens=10)
        )

    async def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                id="mock-model",
                capabilities=ModelCapabilities(streaming=True, embeddings=True)
            )
        ]

    async def health(self) -> ProviderHealth:
        return ProviderHealth(status="ok")
