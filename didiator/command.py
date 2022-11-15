import abc
from typing import Generic, TypeVar

CR = TypeVar("CR")


class Command(abc.ABC, Generic[CR]):
    pass


C = TypeVar("C", bound=Command)


class CommandHandler(abc.ABC, Generic[C, CR]):
    @abc.abstractmethod
    async def __call__(self, command: C) -> CR:
        ...
