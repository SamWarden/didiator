import abc
from collections.abc import Awaitable, Sequence, Callable
from typing import Generic, Type, TypeVar

CR = TypeVar("CR")


class Command(abc.ABC, Generic[CR]):
    pass


C = TypeVar("C", bound=Command)


class CommandHandler(abc.ABC, Generic[C, CR]):
    @abc.abstractmethod
    async def handle(self, command: C) -> CR:
        ...


Middleware = Callable[[Callable[[C, ...], Awaitable[CR]], C], CR]


class CommandDispatcherImpl:
    def __init__(self, middlewares: Sequence[Middleware] = ()) -> None:
        self._handlers: dict[Type[Command], Type[CommandHandler]] = {}
        self._middlewares: Sequence[Middleware] = middlewares

    def register_handler(self, command: Type[C], handler: Type[CommandHandler[C, CR]]) -> None:
        self._handlers[command] = handler

    @property
    def handlers(self) -> dict[Type[Command], Type[CommandHandler]]:
        return self._handlers

    @property
    def middlewares(self) -> tuple[Middleware, ...]:
        return tuple(self._middlewares)
