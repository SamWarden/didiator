import abc
from typing import Any, Generic, TypeVar

RRes = TypeVar("RRes")


class Request(abc.ABC, Generic[RRes]):
    pass


R = TypeVar("R", bound=Request[Any])


class Handler(abc.ABC, Generic[R, RRes]):
    @abc.abstractmethod
    async def __call__(self, request: R) -> RRes:
        ...
