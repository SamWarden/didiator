import abc
from typing import Any, Generic, TypeVar

RES = TypeVar("RES")


class Request(abc.ABC, Generic[RES]):
    pass


R = TypeVar("R", bound=Request[Any])


class RequestHandler(abc.ABC, Generic[R, RES]):
    @abc.abstractmethod
    async def __call__(self, request: R) -> RES:
        ...

#
# class BaseHandler(abc.ABC):
#     @abc.abstractmethod
#     async def handle(self, event: _EventType) -> _ResultType:
#         ...
#
#     async def __call__(self, *args, **kwargs) -> _ResultType:
#         return await self.handle(*args, **kwargs)
#

    # async def __call__(self, *args, **kwargs) -> _ResultType:
    #     return await self.handle(*args, **kwargs)
