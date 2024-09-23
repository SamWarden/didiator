from collections.abc import Sequence

from typing import Any, TypeVar

from didiator.interface import Request
from didiator.interface.entities import Event
from didiator.interface.exceptions import HandlerNotFound
from didiator.interface.handlers import HandlerType
from didiator.interface.handlers.event import EventHandlerType
from didiator.interface.handlers.event import EventListener
from didiator.interface.ioc import Ioc
from didiator.interface.mediator import Mediator
from didiator.middlewares.base import Middleware, wrap_middleware

R = TypeVar("R", bound=Request[Any])
RRes = TypeVar("RRes")
E = TypeVar("E", bound=Event)


class MediatorImpl(Mediator):
    def __init__(self, *, ioc: Ioc, middlewares: list[Middleware]) -> None:
        self._request_handlers: dict[type[Request[Any]], HandlerType[Any, Any]] = {}
        self._event_listeners: list[EventListener] = []
        self._middlewares = middlewares
        self._ioc = ioc

    def register_request_handler(self, request: type[R], handler: HandlerType[R, RRes]) -> None:
        self._request_handlers[request] = handler

    def register_event_handler(self, event: type[E], handler: EventHandlerType[E]) -> None:
        listener = EventListener(event, handler)
        self._event_listeners.append(listener)

    async def send(self, request: Request[RRes]) -> RRes:
        try:
            handler = self._request_handlers[type(request)]
        except KeyError as err:
            raise HandlerNotFound(
                f"Request handler for {type(request).__name__} request is not registered", request,
            ) from err

        async with self._ioc.provide(handler) as initialized_handler:
            wrapped_handler = wrap_middleware(self._middlewares, initialized_handler)
            return await wrapped_handler(request)

    async def publish(self, events: Event | Sequence[Event]) -> None:
        if not isinstance(events, Sequence):
            events = [events]

        for event in events:
            for listener in self._event_listeners:
                if listener.is_listen(event):
                    async with self._ioc.provide(listener.handler) as initialized_handler:
                        wrapped_handler = wrap_middleware(self._middlewares, initialized_handler)
                        return await wrapped_handler(event)
