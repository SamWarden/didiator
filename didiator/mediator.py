from typing import Any, TypeVar

from didiator.command import Command
from didiator.command_dispatcher import CommandDispatcherImpl
from didiator.interface.command_dispatcher import CommandDispatcher
from didiator.interface.mediator import Mediator
from didiator.interface.query_dispatcher import QueryDispatcher
from didiator.query import Query
from didiator.query_dispatcher import QueryDispatcherImpl

CRes = TypeVar("CRes")
QRes = TypeVar("QRes")


class MediatorImpl(Mediator):
    def __init__(
        self,
        command_dispatcher: CommandDispatcher | None = None,
        query_dispatcher: QueryDispatcher | None = None,
        *, extra_data: dict[str, Any] | None = None,
    ):
        if command_dispatcher is None:
            command_dispatcher = CommandDispatcherImpl()
        if query_dispatcher is None:
            query_dispatcher = QueryDispatcherImpl()

        self._command_dispatcher = command_dispatcher
        self._query_dispatcher = query_dispatcher
        self._extra_data = extra_data if extra_data is not None else {}

    @property
    def extra_data(self) -> dict[str, Any]:
        return self._extra_data

    def bind(self, **extra_data: Any) -> "MediatorImpl":
        return MediatorImpl(self._command_dispatcher, self._query_dispatcher, extra_data=self._extra_data | extra_data)

    def unbind(self, *keys: str) -> "MediatorImpl":
        extra_data = {key: val for key, val in self._extra_data.items() if key not in keys}
        return MediatorImpl(self._command_dispatcher, self._query_dispatcher, extra_data=extra_data)

    async def send(self, command: Command[CRes], *args: Any, **kwargs: Any) -> CRes:
        return await self._command_dispatcher.send(command, *args, **kwargs, **self._extra_data)

    async def query(self, query: Query[QRes], *args: Any, **kwargs: Any) -> QRes:
        return await self._query_dispatcher.query(query, *args, **kwargs, **self._extra_data)
