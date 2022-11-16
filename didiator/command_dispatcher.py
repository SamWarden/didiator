from typing import Any, ParamSpec, Type, TypeVar

from didiator.command import Command
from didiator.interface.command_dispatcher import HandlerType
from didiator.request_dispatcher import RequestDispatcherImpl

CR = TypeVar("CR")
C = TypeVar("C", bound=Command[Any])
P = ParamSpec("P")


class CommandDispatcherImpl(RequestDispatcherImpl):
    _handlers: dict[Type[Command[Any]], HandlerType[Any, Any]]

    def register_handler(self, command: Type[C], handler: HandlerType[C, CR]) -> None:
        super().register_handler(command, handler)

    # @property
    # def handlers(self) -> dict[Type[Command[Any]], HandlerType]:
    #     return super().handlers

    async def send(self, command: Command[CR], *args: P.args, **kwargs: P.kwargs) -> CR:
        return await self._handle(command, *args, **kwargs)
