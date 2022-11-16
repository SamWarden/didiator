import abc
from typing import Any, Generic, TypeVar

from didiator.request import Request, Handler

CRes = TypeVar("CRes")


class Command(Request[CRes], abc.ABC, Generic[CRes]):
    pass


C = TypeVar("C", bound=Command[Any])


class CommandHandler(Handler[C, CRes], abc.ABC, Generic[C, CRes]):
    @abc.abstractmethod
    async def __call__(self, command: C) -> CRes:
        ...
