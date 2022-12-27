import abc
from typing import Any, Awaitable, Callable, Generic, Type, TypeVar, Union

from didiator.interface.entities.request import Request

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request[Any])


class Handler(abc.ABC, Generic[R, RRes]):
    @abc.abstractmethod
    async def __call__(self, request: R) -> RRes:
        raise NotImplementedError


HandlerType = Union[Type[Handler[R, RRes]], Callable[..., Awaitable[RRes]]]
