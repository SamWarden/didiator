import abc

from typing import Any, Protocol, TypeVar

from didiator.interface.entities import Request

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request[Any])


class Handler(Protocol[R, RRes]):
    @abc.abstractmethod
    async def __call__(self, request: R) -> RRes:
        raise NotImplementedError


HandlerType = type[Handler[R, RRes]] | Handler[R, RRes]
