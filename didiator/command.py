import abc
from typing import Any, Generic, TypeVar

from didiator.request import Request, RequestHandler

CRES = TypeVar("CRES")


class Command(Request[CRES], abc.ABC, Generic[CRES]):
    pass


C = TypeVar("C", bound=Command[Any])


class CommandHandler(RequestHandler[C, CRES], abc.ABC, Generic[C, CRES]):
    @abc.abstractmethod
    async def __call__(self, command: C) -> CRES:
        ...
