import abc

from typing import Any, Generic, Protocol, TypeVar

from didiator.interface.entities import Event
from .request import Handler

E = TypeVar("E", bound=Event)


class EventHandler(Handler[E, Any], Protocol[E]):
    @abc.abstractmethod
    async def __call__(self, event: E) -> Any:
        raise NotImplementedError


EventHandlerType = type[EventHandler[E]] | EventHandler[E]


class EventListener(Generic[E]):
    def __init__(self, event: type[E], handler: EventHandlerType[E]):
        self._event = event
        self._handler = handler

    def is_listen(self, event: Event) -> bool:
        return isinstance(event, self._event)

    @property
    def event(self) -> type[E]:
        return self._event

    @property
    def handler(self) -> EventHandlerType[E]:
        return self._handler
