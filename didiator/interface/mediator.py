from typing import Any, ParamSpec, Protocol, TypeVar

from didiator.command import Command

Self = TypeVar("Self", bound="BaseMediator")
CR = TypeVar("CR")
C = TypeVar("C", bound=Command[Any])
P = ParamSpec("P")


class BaseMediator(Protocol):
    @property
    def extra_data(self) -> dict[str, Any]:
        raise NotImplementedError

    def bind(self: Self, **extra_data: Any) -> Self:
        raise NotImplementedError

    def unbind(self: Self, *keys: str) -> Self:
        raise NotImplementedError


class CommandMediator(BaseMediator, Protocol):
    async def send(self, command: Command[CR], *args: P.args, **kwargs: P.kwargs) -> CR:
        raise NotImplementedError


class Mediator(BaseMediator, Protocol):
    pass
