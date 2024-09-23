from typing import Protocol, TypeVar

RRes = TypeVar("RRes")


class Request(Protocol[RRes]):
    pass


class Event(Request[None], Protocol):
    pass
