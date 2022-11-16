from typing import Any, Type, TypeVar

from didiator.command import Command
from didiator.interface.command_dispatcher import CommandDispatcher
from didiator.interface.dispatcher import HandlerType
from didiator.interface.exceptions import CommandHandlerNotFound, HandlerNotFound
from didiator.request_dispatcher import RequestDispatcherImpl

CRES = TypeVar("CRES")
C = TypeVar("C", bound=Command[Any])


class CommandDispatcherImpl(RequestDispatcherImpl, CommandDispatcher):
    def register_handler(self, command: Type[C], handler: HandlerType[C, CRES]) -> None:
        super()._register_handler(command, handler)

    async def send(self, command: Command[CRES], *args: Any, **kwargs: Any) -> CRES:
        try:
            return await self._handle(command, *args, **kwargs)
        except HandlerNotFound:
            raise CommandHandlerNotFound()
