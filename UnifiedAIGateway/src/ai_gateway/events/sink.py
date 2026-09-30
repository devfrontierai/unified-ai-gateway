from abc import ABC, abstractmethod
from typing import Any
import structlog

from ai_gateway.events.models import BaseEvent

logger = structlog.get_logger(__name__)

class EventSink(ABC):
    @abstractmethod
    async def publish(self, event: BaseEvent):
        ...

class InMemorySink(EventSink):
    def __init__(self):
        self.events: list[BaseEvent] = []
        
    async def publish(self, event: BaseEvent):
        self.events.append(event)

class StructuredLogSink(EventSink):
    async def publish(self, event: BaseEvent):
        logger.info("gateway_event", event_type=event.__class__.__name__, **event.model_dump())
