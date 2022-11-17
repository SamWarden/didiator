import abc
from typing import Any, Generic, TypeVar

from didiator.interface.entities.command import Command

from .request import Handler

CRes = TypeVar("CRes")
C = TypeVar("C", bound=Command[Any])


class CommandHandler(Handler[C, CRes], abc.ABC, Generic[C, CRes]):
    @abc.abstractmethod
    async def __call__(self, command: C) -> CRes:
        ...
