from collections.abc import Sequence
from typing import Any, Protocol, Type, TypeVar

from didiator.interface.entities.command import Command
from didiator.interface.entities.event import Event
from didiator.interface.entities.query import Query
from didiator.interface.handlers.command import CommandHandlerType
from didiator.interface.handlers.event import EventHandlerType
from didiator.interface.handlers.query import QueryHandlerType

Self = TypeVar("Self", bound="BaseMediator")
C = TypeVar("C", bound=Command[Any])
CRes = TypeVar("CRes")
Q = TypeVar("Q", bound=Query[Any])
QRes = TypeVar("QRes")
E = TypeVar("E", bound=Event)


class BaseMediator(Protocol):
    @property
    def extra_data(self) -> dict[str, Any]:
        raise NotImplementedError

    def bind(self: Self, **extra_data: Any) -> Self:
        raise NotImplementedError

    def unbind(self: Self, *keys: str) -> Self:
        raise NotImplementedError


class CommandMediator(BaseMediator, Protocol):
    async def send(self, command: Command[CRes], *args: Any, **kwargs: Any) -> CRes:
        raise NotImplementedError

    def register_command_handler(self, command: Type[C], handler: CommandHandlerType[C, CRes]) -> None:
        raise NotImplementedError


class QueryMediator(BaseMediator, Protocol):
    async def query(self, query: Query[QRes], *args: Any, **kwargs: Any) -> QRes:
        raise NotImplementedError

    def register_query_handler(self, query: Type[Q], handler: QueryHandlerType[Q, QRes]) -> None:
        raise NotImplementedError


class EventMediator(BaseMediator, Protocol):
    async def publish(self, events: Event | Sequence[Event], *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    def register_event_handler(self, event: Type[E], handler: EventHandlerType[E]) -> None:
        raise NotImplementedError


class Mediator(CommandMediator, QueryMediator, EventMediator, BaseMediator, Protocol):
    pass
