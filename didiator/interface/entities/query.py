import abc
from typing import Generic, TypeVar

from didiator.interface.entities.request import Request

QRes = TypeVar("QRes")


class Query(Request[QRes], abc.ABC, Generic[QRes]):
    pass
