from typing import Any, Protocol, Type, TypeVar

from didiator.interface.entities.command import Command
from didiator.interface.dispatchers.request import Dispatcher
from didiator.interface.handlers import HandlerType

C = TypeVar("C", bound=Command[Any])
CRes = TypeVar("CRes")


class CommandDispatcher(Dispatcher, Protocol):
    @property
    def handlers(self) -> dict[Type[Command[Any]], HandlerType[Any, Any]]:
        raise NotImplementedError

    def register_handler(self, command: Type[C], handler: HandlerType[C, CRes]) -> None:
        raise NotImplementedError

    async def send(self, command: Command[CRes], *args: Any, **kwargs: Any) -> CRes:
        raise NotImplementedError
