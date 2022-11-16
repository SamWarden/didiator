from typing import Any, ParamSpec, Protocol, TypeVar

from didiator.command import Command

CR = TypeVar("CR")
C = TypeVar("C", bound=Command[Any])
P = ParamSpec("P")


class Mediator(Protocol):
    @property
    def extra_data(self) -> dict[str, Any]:
        raise NotImplementedError

    def bind(self, **extra_data: Any) -> "Mediator":
        raise NotImplementedError

    def unbind(self, *keys: str) -> "Mediator":
        raise NotImplementedError

    async def send(self, command: Command[CR], *args: P.args, **kwargs: P.kwargs) -> CR:
        raise NotImplementedError
