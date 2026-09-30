import time
import json
import httpx
from typing import AsyncIterator, Any

from ai_gateway.core.request import ChatRequest, EmbeddingRequest
from ai_gateway.core.response import (
    ChatResponse, ChatChunk, EmbeddingResponse,
    ChatChoice, ChatChunkChoice, ChatUsage, EmbeddingData
)
from ai_gateway.core.capabilities import ModelCapabilities
from ai_gateway.providers.base import ModelProvider, ModelInfo, ProviderHealth

class OpenAIProvider(ModelProvider):
    """OpenAI provider implementation."""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=httpx.Timeout(60.0)
        )

    def _convert_chat_request(self, request: ChatRequest) -> dict[str, Any]:
        payload = {
            "model": request.model,
            "messages": [
                {k: v for k, v in m.model_dump().items() if v is not None}
                for m in request.messages
            ]
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.tools is not None:
            payload["tools"] = [t.model_dump() for t in request.tools]
        if request.tool_choice is not None:
            payload["tool_choice"] = request.tool_choice
        if request.response_format is not None:
            payload["response_format"] = request.response_format
        if request.stream:
            payload["stream"] = True

        return payload

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        payload = self._convert_chat_request(request)
        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        
        choices = []
        for c in data.get("choices", []):
            choices.append(ChatChoice(
                index=c["index"],
                message=c["message"],
                finish_reason=c.get("finish_reason")
            ))
            
        usage_data = data.get("usage", {})
        usage = ChatUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0)
        ) if usage_data else None

        return ChatResponse(
            id=data["id"],
            model=data["model"],
            created=data["created"],
            choices=choices,
            usage=usage
        )

    async def stream_chat_completion(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        payload = self._convert_chat_request(request)
        
        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                line = line.strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choices = []
                        for c in data.get("choices", []):
                            choices.append(ChatChunkChoice(
                                index=c["index"],
                                delta=c["delta"],
                                finish_reason=c.get("finish_reason")
                            ))
                            
                        # Extract usage if present (stream_options=include_usage could be supported in future)
                        usage_data = data.get("usage")
                        usage = ChatUsage(
                            prompt_tokens=usage_data.get("prompt_tokens", 0),
                            completion_tokens=usage_data.get("completion_tokens", 0),
                            total_tokens=usage_data.get("total_tokens", 0)
                        ) if usage_data else None

                        yield ChatChunk(
                            id=data["id"],
                            model=data["model"],
                            created=data["created"],
                            choices=choices,
                            usage=usage
                        )
                    except json.JSONDecodeError:
                        continue

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        payload = {
            "model": request.model,
            "input": request.input
        }
        if request.dimensions:
            payload["dimensions"] = request.dimensions

        response = await self.client.post("/embeddings", json=payload)
        response.raise_for_status()
        data = response.json()
        
        embeddings_data = []
        for d in data.get("data", []):
            embeddings_data.append(EmbeddingData(
                index=d["index"],
                embedding=d["embedding"]
            ))

        usage_data = data.get("usage", {})
        usage = ChatUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0)
        )

        return EmbeddingResponse(
            model=data["model"],
            data=embeddings_data,
            usage=usage
        )

    async def list_models(self) -> list[ModelInfo]:
        # Return common OpenAI models mapping
        return [
            ModelInfo(id="gpt-4o", capabilities=ModelCapabilities(streaming=True, tools=True, vision=True, structured_output=True)),
            ModelInfo(id="gpt-4-turbo", capabilities=ModelCapabilities(streaming=True, tools=True, vision=True, structured_output=True)),
            ModelInfo(id="gpt-3.5-turbo", capabilities=ModelCapabilities(streaming=True, tools=True)),
            ModelInfo(id="text-embedding-3-small", capabilities=ModelCapabilities(embeddings=True)),
            ModelInfo(id="text-embedding-3-large", capabilities=ModelCapabilities(embeddings=True)),
        ]

    async def health(self) -> ProviderHealth:
        try:
            # Just test /models endpoint for health check
            response = await self.client.get("/models")
            response.raise_for_status()
            return ProviderHealth(status="ok")
        except Exception as e:
            return ProviderHealth(status="error", details={"error": str(e)})

    async def close(self):
        await self.client.aclose()
