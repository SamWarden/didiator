import abc
from typing import Callable, Generic, Type, TypeVar

CR = TypeVar("CR")


class Command(abc.ABC, Generic[CR]):
    pass


C = TypeVar("C", bound=Command)


class CommandHandler(abc.ABC, Generic[C, CR]):
    @abc.abstractmethod
    async def handle(self, command: C) -> CR:
        ...


Middleware = Callable


class CommandDispatcherImpl:
    def __init__(self) -> None:
        self._handlers: dict[Type[Command], Type[CommandHandler]] = {}
        self._middlewares: list[Middleware] = []

    def register_handler(self, command: Type[C], handler: Type[CommandHandler[C, CR]]) -> None:
        self._handlers[command] = handler

    @property
    def handlers(self) -> dict[Type[Command], Type[CommandHandler]]:
        return self._handlers

    @property
    def middlewares(self) -> tuple[Middleware, ...]:
        return tuple(self._middlewares)
