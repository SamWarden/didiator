from typing import Any, Protocol, Type, TypeVar

from didiator.command import Command
from didiator.interface.dispatcher import Dispatcher, HandlerType

CRes = TypeVar("CRes")
C = TypeVar("C", bound=Command[Any])

# HandlerType = Callable[[C], Awaitable[CRes]] | Type[RequestHandler[C, CRes]]


class CommandDispatcher(Dispatcher, Protocol):
    @property
    def handlers(self) -> dict[Type[Command[Any]], HandlerType[Any, Any]]:
        raise NotImplementedError

    def register_handler(self, command: Type[C], handler: HandlerType[C, CRes]) -> None:
        raise NotImplementedError

    async def send(self, command: Command[CRes], *args: Any, **kwargs: Any) -> CRes:
        raise NotImplementedError
