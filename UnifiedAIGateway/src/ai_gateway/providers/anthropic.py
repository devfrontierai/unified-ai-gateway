import json
import httpx
from typing import AsyncIterator, Any
import time

from ai_gateway.core.request import ChatRequest, EmbeddingRequest
from ai_gateway.core.response import (
    ChatResponse, ChatChunk, EmbeddingResponse,
    ChatChoice, ChatChunkChoice, ChatUsage, EmbeddingData
)
from ai_gateway.core.capabilities import ModelCapabilities
from ai_gateway.providers.base import ModelProvider, ModelInfo, ProviderHealth

class AnthropicProvider(ModelProvider):
    """Anthropic provider implementation."""

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            timeout=httpx.Timeout(60.0)
        )

    def _convert_chat_request(self, request: ChatRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_tokens or 4096,  # required by Anthropic
        }
        
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.stream:
            payload["stream"] = True

        system_messages = [m for m in request.messages if m.role == "system"]
        if system_messages:
            payload["system"] = "\n\n".join(str(m.content) for m in system_messages if m.content)

        messages = []
        for m in request.messages:
            if m.role == "system":
                continue
            
            # Simplified translation, in reality needs mapping for tools/multimodal
            role = "user" if m.role == "user" else "assistant"
            messages.append({
                "role": role,
                "content": m.content
            })
            
        payload["messages"] = messages
        
        # Tools translation would go here

        return payload

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        payload = self._convert_chat_request(request)
        response = await self.client.post("/messages", json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Anthropic response to Canonical translation
        content_blocks = data.get("content", [])
        text_content = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        
        usage_data = data.get("usage", {})
        usage = ChatUsage(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0)
        )
        
        return ChatResponse(
            id=data.get("id", f"msg_{int(time.time())}"),
            model=data.get("model", request.model),
            created=int(time.time()),
            choices=[
                ChatChoice(
                    index=0,
                    message={"role": "assistant", "content": text_content},
                    finish_reason=data.get("stop_reason", "stop")
                )
            ],
            usage=usage
        )

    async def stream_chat_completion(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        payload = self._convert_chat_request(request)
        
        resp_id = ""
        model_name = request.model
        created = int(time.time())
        
        async with self.client.stream("POST", "/messages", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                    
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                    
                try:
                    data = json.loads(data_str)
                    event_type = data.get("type")
                    
                    if event_type == "message_start":
                        msg = data.get("message", {})
                        resp_id = msg.get("id", "")
                        model_name = msg.get("model", request.model)
                        
                        # We could yield a chunk with empty delta here if needed
                        
                    elif event_type == "content_block_delta":
                        delta = data.get("delta", {})
                        text = delta.get("text", "")
                        if text:
                            yield ChatChunk(
                                id=resp_id,
                                model=model_name,
                                created=created,
                                choices=[
                                    ChatChunkChoice(
                                        index=data.get("index", 0),
                                        delta={"role": "assistant", "content": text}
                                    )
                                ]
                            )
                            
                    elif event_type == "message_delta":
                        usage = data.get("usage", {})
                        stop_reason = data.get("delta", {}).get("stop_reason")
                        
                        yield ChatChunk(
                            id=resp_id,
                            model=model_name,
                            created=created,
                            choices=[
                                ChatChunkChoice(
                                    index=0,
                                    delta={},
                                    finish_reason=stop_reason
                                )
                            ],
                            usage=ChatUsage(
                                prompt_tokens=usage.get("input_tokens", 0),
                                completion_tokens=usage.get("output_tokens", 0)
                            ) if usage else None
                        )
                        
                except json.JSONDecodeError:
                    continue

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        # Anthropic doesn't have an embeddings API natively yet, but Voyage AI is their partner.
        # For this prototype, we'll raise an error or mock it.
        raise NotImplementedError("Embeddings not natively supported by Anthropic")

    async def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(id="claude-3-5-sonnet-20240620", capabilities=ModelCapabilities(streaming=True, tools=True, vision=True)),
            ModelInfo(id="claude-3-opus-20240229", capabilities=ModelCapabilities(streaming=True, tools=True, vision=True)),
            ModelInfo(id="claude-3-haiku-20240307", capabilities=ModelCapabilities(streaming=True, tools=True, vision=True)),
        ]

    async def health(self) -> ProviderHealth:
        # Just a basic ping or fallback since Anthropic doesn't have a simple health/models endpoint that is unauthenticated in the same way
        return ProviderHealth(status="ok")

    async def close(self):
        await self.client.aclose()
