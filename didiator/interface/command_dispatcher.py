from typing import Any, ParamSpec, Protocol, Type, TypeVar

from didiator.command import Command
from didiator.interface.dispatcher import Dispatcher, HandlerType

CRES = TypeVar("CRES")
C = TypeVar("C", bound=Command[Any])
P = ParamSpec("P")

# HandlerType = Callable[[C], Awaitable[CRES]] | Type[RequestHandler[C, CRES]]


class CommandDispatcher(Dispatcher, Protocol):
    @property
    def handlers(self) -> dict[Type[Command[Any]], HandlerType[Any, Any]]:
        raise NotImplementedError

    def register_handler(self, command: Type[C], handler: HandlerType[C, CRES]) -> None:
        raise NotImplementedError

    async def send(self, command: Command[CRES], *args: P.args, **kwargs: P.kwargs) -> CRES:
        raise NotImplementedError
