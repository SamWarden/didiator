import abc
from typing import Any, Awaitable, Callable, Generic, Type, TypeVar, Union

from didiator.interface.entities.event import Event

from .request import Handler

E = TypeVar("E", bound=Event)


class EventHandler(Handler[E, Any], abc.ABC, Generic[E]):
    @abc.abstractmethod
    async def __call__(self, event: E) -> Any:
        raise NotImplementedError


EventHandlerType = Union[Type[EventHandler[E]], Callable[..., Awaitable[Any]]]
