import abc
from typing import Generic, TypeVar

RRes = TypeVar("RRes")


class Request(abc.ABC, Generic[RRes]):
    pass
