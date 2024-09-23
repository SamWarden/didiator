from collections.abc import Sequence

from didiator.interface.entities import Event, Request
from typing import Any, Protocol, Type, TypeVar

from didiator.interface.handlers import HandlerType
from didiator.interface.handlers.event import EventHandlerType

R = TypeVar("R", bound=Request[Any])
RRes = TypeVar("RRes")
E = TypeVar("E", bound=Event)


class Mediator(Protocol):
    def register_request_handler(self, request: Type[R], handler: HandlerType[R, RRes]) -> None:
        raise NotImplementedError

    def register_event_handler(self, event: Type[E], handler: EventHandlerType[E]) -> None:
        raise NotImplementedError

    async def send(self, request: Request[RRes]) -> RRes:
        raise NotImplementedError

    async def publish(self, events: Event | Sequence[Event]) -> None:
        raise NotImplementedError
