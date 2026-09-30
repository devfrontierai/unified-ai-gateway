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

class GeminiProvider(ModelProvider):
    """Google Gemini provider implementation."""

    def __init__(self, api_key: str, base_url: str = "https://generativelanguage.googleapis.com/v1beta"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(60.0)
        )

    def _convert_chat_request(self, request: ChatRequest) -> dict[str, Any]:
        contents = []
        system_instruction = None
        
        for m in request.messages:
            if m.role == "system":
                system_instruction = {"parts": [{"text": str(m.content)}]}
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": str(m.content)}]
                })
                
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {}
        }
        
        if system_instruction:
            payload["systemInstruction"] = system_instruction
            
        if request.temperature is not None:
            payload["generationConfig"]["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens
            
        return payload

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        payload = self._convert_chat_request(request)
        url = f"/models/{request.model}:generateContent?key={self.api_key}"
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        candidates = data.get("candidates", [])
        text_content = ""
        finish_reason = "stop"
        
        if candidates:
            first_candidate = candidates[0]
            parts = first_candidate.get("content", {}).get("parts", [])
            if parts:
                text_content = parts[0].get("text", "")
            finish_reason = first_candidate.get("finishReason", "stop").lower()
            
        usage_data = data.get("usageMetadata", {})
        usage = ChatUsage(
            prompt_tokens=usage_data.get("promptTokenCount", 0),
            completion_tokens=usage_data.get("candidatesTokenCount", 0),
            total_tokens=usage_data.get("totalTokenCount", 0)
        )
        
        return ChatResponse(
            id=f"gemini-{int(time.time())}",
            model=request.model,
            created=int(time.time()),
            choices=[
                ChatChoice(
                    index=0,
                    message={"role": "assistant", "content": text_content},
                    finish_reason=finish_reason
                )
            ],
            usage=usage
        )

    async def stream_chat_completion(self, request: ChatRequest) -> AsyncIterator[ChatChunk]:
        payload = self._convert_chat_request(request)
        url = f"/models/{request.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        
        created = int(time.time())
        resp_id = f"gemini-{created}"
        
        async with self.client.stream("POST", url, json=payload) as response:
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
                    candidates = data.get("candidates", [])
                    if candidates:
                        first_candidate = candidates[0]
                        parts = first_candidate.get("content", {}).get("parts", [])
                        text = parts[0].get("text", "") if parts else ""
                        finish_reason = first_candidate.get("finishReason")
                        
                        yield ChatChunk(
                            id=resp_id,
                            model=request.model,
                            created=created,
                            choices=[
                                ChatChunkChoice(
                                    index=first_candidate.get("index", 0),
                                    delta={"role": "assistant", "content": text},
                                    finish_reason=finish_reason.lower() if finish_reason else None
                                )
                            ]
                        )
                except json.JSONDecodeError:
                    continue

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        input_texts = request.input if isinstance(request.input, list) else [request.input]
        url = f"/models/{request.model}:batchEmbedContents?key={self.api_key}"
        
        requests = [{"model": f"models/{request.model}", "content": {"parts": [{"text": text}]}} for text in input_texts]
        
        payload = {"requests": requests}
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        embeddings = data.get("embeddings", [])
        
        data_res = []
        for i, emb in enumerate(embeddings):
            data_res.append(EmbeddingData(
                index=i,
                embedding=emb.get("values", [])
            ))
            
        return EmbeddingResponse(
            model=request.model,
            data=data_res,
            usage=ChatUsage(prompt_tokens=0, total_tokens=0) # Gemini doesn't always return token counts for embeddings
        )

    async def list_models(self) -> list[ModelInfo]:
        url = f"/models?key={self.api_key}"
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        
        models = []
        for m in data.get("models", []):
            models.append(ModelInfo(
                id=m["name"].replace("models/", ""),
                capabilities=ModelCapabilities(streaming=True)
            ))
        return models

    async def health(self) -> ProviderHealth:
        return ProviderHealth(status="ok")

    async def close(self):
        await self.client.aclose()
