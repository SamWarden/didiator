import abc
from collections.abc import Awaitable, Callable
from typing import Any, Generic, Type, TypeVar, Union

from didiator.interface.entities.command import Command

from .request import Handler

CRes = TypeVar("CRes")
C = TypeVar("C", bound=Command[Any])


class CommandHandler(Handler[C, CRes], abc.ABC, Generic[C, CRes]):
    @abc.abstractmethod
    async def __call__(self, command: C) -> CRes:
        raise NotImplementedError


CommandHandlerType = Union[Type[CommandHandler[C, CRes]], Callable[..., Awaitable[CRes]]]
