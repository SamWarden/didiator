from collections.abc import Awaitable, Callable
from typing import ParamSpec, Type, TypeVar

from didiator.command import Command, CommandHandler
from didiator.middlewares.base import Middleware

CR = TypeVar("CR")
C = TypeVar("C", bound=Command)
P = ParamSpec("P")

HandlerType = Callable[[C], Awaitable[CR]] | Type[CommandHandler[C, CR]]


class DataAdderMiddlewareMock(Middleware):
    def __init__(self, **kwargs):
        self._additional_kwargs = kwargs

    async def __call__(
        self,
        handler: HandlerType,
        command: C,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> CR:
        kwargs |= self._additional_kwargs
        return await self._call(handler, command, *args, **kwargs)


class DataRemoverMiddlewareMock(Middleware):
    def __init__(self, *args):
        self._removable_args = args

    async def __call__(
        self,
        handler: HandlerType,
        command: C,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> CR:
        kwargs = {key: val for key, val in kwargs.items() if key not in self._removable_args}
        return await self._call(handler, command, *args, **kwargs)
