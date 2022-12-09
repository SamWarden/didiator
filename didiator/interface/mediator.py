from typing import Any, Protocol, Type, TypeVar

from didiator.interface.entities.command import Command
from didiator.interface.entities.query import Query
from didiator.interface.handlers import HandlerType

Self = TypeVar("Self", bound="BaseMediator")
C = TypeVar("C", bound=Command)
CRes = TypeVar("CRes")
Q = TypeVar("Q", bound=Query)
QRes = TypeVar("QRes")


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

    def register_command_handler(self, command: Type[C], handler: HandlerType[C, CRes]) -> None:
        raise NotImplementedError


class QueryMediator(BaseMediator, Protocol):
    async def query(self, query: Query[QRes], *args: Any, **kwargs: Any) -> QRes:
        raise NotImplementedError

    def register_query_handler(self, query: Type[Q], handler: HandlerType[Q, QRes]) -> None:
        raise NotImplementedError


class Mediator(CommandMediator, QueryMediator, BaseMediator, Protocol):
    pass
