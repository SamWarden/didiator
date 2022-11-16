from typing import Any, ParamSpec, TypeVar

from didiator.command import Command
from didiator.dispatcher import CommandDispatcherImpl
from didiator.interface.dispatcher import CommandDispatcher
from didiator.interface.mediator import Mediator

CR = TypeVar("CR")
C = TypeVar("C", bound=Command[Any])
P = ParamSpec("P")


class MediatorImpl(Mediator):
    def __init__(
        self, command_dispatcher: CommandDispatcher | None = None,
        *, extra_data: dict[str, Any] | None = None,
    ):
        if command_dispatcher is None:
            command_dispatcher = CommandDispatcherImpl()

        self._command_dispatcher = command_dispatcher
        self._extra_data = extra_data if extra_data is not None else {}

    @property
    def extra_data(self) -> dict[str, Any]:
        return self._extra_data

    def bind(self, **extra_data: Any) -> "MediatorImpl":
        return MediatorImpl(self._command_dispatcher, extra_data=self._extra_data | extra_data)

    def unbind(self, *keys: str) -> "MediatorImpl":
        extra_data = {key: val for key, val in self._extra_data.items() if key not in keys}
        return MediatorImpl(self._command_dispatcher, extra_data=extra_data)

    async def send(self, command: Command[CR], *args: P.args, **kwargs: P.kwargs) -> CR:
        return await self._command_dispatcher.send(command, *args, **kwargs, **self._extra_data)
