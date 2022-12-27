import abc
from collections.abc import Awaitable, Callable
from typing import Any, Generic, Type, TypeVar, Union

from didiator.interface.entities.query import Query

from .request import Handler

QRes = TypeVar("QRes")
Q = TypeVar("Q", bound=Query[Any])


class QueryHandler(Handler[Q, QRes], abc.ABC, Generic[Q, QRes]):
    @abc.abstractmethod
    async def __call__(self, query: Q) -> QRes:
        raise NotImplementedError


QueryHandlerType = Union[Type[QueryHandler[Q, QRes]], Callable[..., Awaitable[QRes]]]
