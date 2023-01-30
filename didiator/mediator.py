from collections.abc import Sequence
from typing import Any, Type, TypeVar

from didiator.dispatchers.command import CommandDispatcherImpl
from didiator.observers.event import EventObserverImpl
from didiator.dispatchers.query import QueryDispatcherImpl
from didiator.interface.observers.event import EventObserver, Listener
from didiator.interface.entities.command import Command
from didiator.interface.dispatchers.command import CommandDispatcher
from didiator.interface.dispatchers.query import QueryDispatcher
from didiator.interface.entities.event import Event
from didiator.interface.entities.query import Query
from didiator.interface.handlers.command import CommandHandlerType
from didiator.interface.handlers.event import EventHandlerType
from didiator.interface.handlers.query import QueryHandlerType
from didiator.interface.mediator import Mediator

C = TypeVar("C", bound=Command[Any])
CRes = TypeVar("CRes")
Q = TypeVar("Q", bound=Query[Any])
QRes = TypeVar("QRes")
E = TypeVar("E", bound=Event)


class MediatorImpl(Mediator):
    def __init__(
        self,
        command_dispatcher: CommandDispatcher | None = None,
        query_dispatcher: QueryDispatcher | None = None,
        event_observer: EventObserver | None = None,
        *, extra_data: dict[str, Any] | None = None,
    ):
        if command_dispatcher is None:
            command_dispatcher = CommandDispatcherImpl()
        if query_dispatcher is None:
            query_dispatcher = QueryDispatcherImpl()
        if event_observer is None:
            event_observer = EventObserverImpl()

        self._command_dispatcher = command_dispatcher
        self._query_dispatcher = query_dispatcher
        self._event_observer = event_observer
        self._extra_data = extra_data if extra_data is not None else {}

    @property
    def extra_data(self) -> dict[str, Any]:
        return self._extra_data

    def bind(self, **extra_data: Any) -> "MediatorImpl":
        return MediatorImpl(
            self._command_dispatcher.copy(),
            self._query_dispatcher.copy(),
            self._event_observer.copy(),
            extra_data=self._extra_data | extra_data,
        )

    def unbind(self, *keys: str) -> "MediatorImpl":
        extra_data = {key: val for key, val in self._extra_data.items() if key not in keys}
        return MediatorImpl(
            self._command_dispatcher.copy(),
            self._query_dispatcher.copy(),
            self._event_observer.copy(),
            extra_data=extra_data,
        )

    def register_command_handler(self, command: Type[C], handler: CommandHandlerType[C, CRes]) -> None:
        self._command_dispatcher.register_handler(command, handler)

    def register_query_handler(self, query: Type[Q], handler: QueryHandlerType[Q, QRes]) -> None:
        self._query_dispatcher.register_handler(query, handler)

    def register_event_handler(self, event: Type[E], handler: EventHandlerType[E]) -> None:
        listener = Listener(event, handler)
        self._event_observer.register_listener(listener)

    async def send(self, command: Command[CRes], *args: Any, **kwargs: Any) -> CRes:
        kwargs = self._extra_data | kwargs
        return await self._command_dispatcher.send(command, *args, **kwargs)

    async def query(self, query: Query[QRes], *args: Any, **kwargs: Any) -> QRes:
        kwargs = self._extra_data | kwargs
        return await self._query_dispatcher.query(query, *args, **kwargs)

    async def publish(self, events: Event | Sequence[Event], *args: Any, **kwargs: Any) -> None:
        if isinstance(events, Event):
            events = (events,)
        kwargs = self._extra_data | kwargs
        await self._event_observer.publish(events, *args, **kwargs)
