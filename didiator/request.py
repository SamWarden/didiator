import abc
from typing import Any, Generic, TypeVar

RES = TypeVar("RES")


class Request(abc.ABC, Generic[RES]):
    pass


R = TypeVar("R", bound=Request[Any])


class CommandHandler(abc.ABC, Generic[R, RES]):
    @abc.abstractmethod
    async def __call__(self, request: R) -> RES:
        ...
