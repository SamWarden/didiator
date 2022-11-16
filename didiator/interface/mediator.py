from typing import Any, Protocol, TypeVar

from didiator.command import Command
from didiator.query import Query

Self = TypeVar("Self", bound="BaseMediator")
CRes = TypeVar("CRes")
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


class QueryMediator(BaseMediator, Protocol):
    async def query(self, query: Query[QRes], *args: Any, **kwargs: Any) -> CRes:
        raise NotImplementedError


class Mediator(CommandMediator, QueryMediator, BaseMediator, Protocol):
    pass
