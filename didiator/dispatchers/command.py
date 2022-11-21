from typing import Any, Type, TypeVar

from didiator.interface.entities.command import Command
from didiator.interface.dispatchers.command import CommandDispatcher
from didiator.interface.handlers.request import HandlerType
from didiator.interface.exceptions import CommandHandlerNotFound, HandlerNotFound
from didiator.dispatchers.request import RequestDispatcherImpl

CRes = TypeVar("CRes")
C = TypeVar("C", bound=Command[Any])


class CommandDispatcherImpl(RequestDispatcherImpl, CommandDispatcher):
    def register_handler(self, command: Type[C], handler: HandlerType[C, CRes]) -> None:
        super()._register_handler(command, handler)

    async def send(self, command: Command[CRes], *args: Any, **kwargs: Any) -> CRes:
        try:
            return await self._handle(command, *args, **kwargs)
        except HandlerNotFound:
            raise CommandHandlerNotFound(f"Command handler for {type(command).__name__} command is not registered", command)
