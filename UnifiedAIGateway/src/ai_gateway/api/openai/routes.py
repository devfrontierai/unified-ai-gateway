from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
import uuid
import json
from typing import AsyncGenerator

from ai_gateway.api.openai.models import OpenAIChatRequest, OpenAIEmbeddingRequest
from ai_gateway.core.request import ChatRequest, Message, EmbeddingRequest
from ai_gateway.routing.engine import RoutingEngine
from ai_gateway.core.pipeline import ExecutionPipeline
from ai_gateway.core.context import GatewayContext
from ai_gateway.core.response import ChatChunk

router = APIRouter()

def convert_chat_request(req: OpenAIChatRequest, request_id: str) -> ChatRequest:
    messages = []
    for m in req.messages:
        messages.append(Message(
            role=m.role,
            content=m.content,
            name=m.name,
            tool_calls=m.tool_calls,
            tool_call_id=m.tool_call_id
        ))
        
    return ChatRequest(
        request_id=request_id,
        tenant_id="default-tenant",  # In future, from auth middleware
        user_id=req.user,
        model=req.model,
        messages=messages,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        stream=req.stream,
        response_format=req.response_format,
    )

async def stream_generator(generator) -> AsyncGenerator[str, None]:
    async for chunk in generator:
        if isinstance(chunk, ChatChunk):
            yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
    yield "data: [DONE]\n\n"

@router.post("/chat/completions")
async def chat_completions(req: Request, request: OpenAIChatRequest):
    req_id = f"req-{uuid.uuid4().hex}"
    internal_req = convert_chat_request(request, req_id)
    
    pipeline: ExecutionPipeline = req.app.state.pipeline
    context = GatewayContext(
        request_id=req_id,
        tenant_id="default-tenant",
        user_id=request.user,
        request=internal_req
    )
    
    try:
        result = await pipeline.execute_chat(context)
        
        if request.stream:
            return StreamingResponse(
                stream_generator(result),
                media_type="text/event-stream"
            )
        else:
            return result.model_dump(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/embeddings")
async def embeddings(req: Request, request: OpenAIEmbeddingRequest):
    req_id = f"req-{uuid.uuid4().hex}"
    
    internal_req = EmbeddingRequest(
        request_id=req_id,
        tenant_id="default-tenant",
        user_id=request.user,
        model=request.model,
        input=request.input,
        dimensions=request.dimensions
    )
    
    pipeline: ExecutionPipeline = req.app.state.pipeline
    context = GatewayContext(
        request_id=req_id,
        tenant_id="default-tenant",
        user_id=request.user,
        request=internal_req
    )
    
    try:
        result = await pipeline.execute_embeddings(context)
        return result.model_dump(exclude_none=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models(req: Request):
    # Return configured alias names from config
    config = req.app.state.gateway_config
    
    models = list(config.models.keys()) + list(config.routing.keys())
    # Remove duplicates
    models = list(set(models))
    
    return {
        "object": "list",
        "data": [
            {
                "id": m,
                "object": "model",
                "created": 1677610602,
                "owned_by": "ai-gateway"
            } for m in models
        ]
    }
