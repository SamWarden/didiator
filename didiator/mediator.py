from typing import Any, Type, TypeVar

from didiator.dispatchers.command import CommandDispatcherImpl
from didiator.dispatchers.query import QueryDispatcherImpl
from didiator.interface.entities.command import Command
from didiator.interface.dispatchers.command import CommandDispatcher
from didiator.interface.dispatchers.query import QueryDispatcher
from didiator.interface.entities.query import Query
from didiator.interface.handlers import HandlerType
from didiator.interface.mediator import Mediator

C = TypeVar("C", bound=Command)
CRes = TypeVar("CRes")
Q = TypeVar("Q", bound=Query)
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

    def register_command_handler(self, command: Type[C], handler: HandlerType[C, CRes]) -> None:
        self._command_dispatcher.register_handler(command, handler)

    def register_query_handler(self, query: Type[Q], handler: HandlerType[Q, QRes]) -> None:
        self._query_dispatcher.register_handler(query, handler)

    async def send(self, command: Command[CRes], *args: Any, **kwargs: Any) -> CRes:
        return await self._command_dispatcher.send(command, *args, **kwargs, **self._extra_data)

    async def query(self, query: Query[QRes], *args: Any, **kwargs: Any) -> QRes:
        return await self._query_dispatcher.query(query, *args, **kwargs, **self._extra_data)
