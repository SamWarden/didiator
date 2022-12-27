from typing import Any, Protocol, TypeVar
import logging

from didiator.interface.entities.command import Command
from didiator.interface.entities.event import Event
from didiator.interface.entities.request import Request
from didiator.interface.entities.query import Query
from didiator.interface.handlers import HandlerType
from didiator.middlewares import Middleware

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request[Any])


class Logger(Protocol):
    def log(self, level: int, msg: str, *args: Any, extra: dict[str, Any] | None = None) -> None:
        raise NotImplementedError


class LoggingMiddleware(Middleware):
    def __init__(self, logger: Logger | str = __name__, level: int | str = logging.DEBUG):
        if isinstance(logger, str):
            logger = logging.getLogger(logger)

        self._logger: Logger = logger
        self._level: int = logging.getLevelName(level) if isinstance(level, str) else level

    async def __call__(
        self,
        handler: HandlerType[R, RRes],
        request: R,
        *args: Any,
        **kwargs: Any,
    ) -> RRes:
        if isinstance(request, Command):
            self._logger.log(self._level, "Send %s command", type(request).__name__, extra={"command": request})
        elif isinstance(request, Query):
            self._logger.log(self._level, "Make %s query", type(request).__name__, extra={"query": request})
        elif isinstance(request, Event):
            self._logger.log(self._level, "Publish %s event", type(request).__name__, extra={"event": request})
        else:
            self._logger.log(self._level, "Execute %s request", type(request).__name__, extra={"request": request})

        res = await self._call(handler, request, *args, **kwargs)
        if isinstance(request, Command):
            self._logger.log(
                self._level, "Command %s sent. Result: %s", type(request).__name__, res, extra={"result": res},
            )
        elif isinstance(request, Query):
            self._logger.log(
                self._level, "Query %s made. Result: %s", type(request).__name__, res, extra={"result": res},
            )
        elif isinstance(request, Event):
            self._logger.log(self._level, "Event %s published", type(request).__name__, extra={"event": request})
        else:
            self._logger.log(
                self._level, "Request %s executed. Result: %s", type(request).__name__, res, extra={"result": res},
            )

        return res
