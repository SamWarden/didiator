import abc
from typing import Generic, TypeVar

QR = TypeVar("QR")


class Query(abc.ABC, Generic[QR]):
    pass


Q = TypeVar("Q", bound=Query)


class QueryHandler(abc.ABC, Generic[Q, QR]):
    @abc.abstractmethod
    async def __call__(self, query: Q) -> QR:
        ...
