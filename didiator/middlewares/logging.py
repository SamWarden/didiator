from typing import Any, Protocol, TypeVar
import logging

from didiator import Command, Query
from didiator.interface.entities.request import Request
from didiator.interface.handlers import HandlerType
from didiator.middlewares import Middleware

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request)


class Logger(Protocol):
    def debug(self, msg: str, *, extra: dict[str, Any] | None = None) -> None:
        ...


class LoggingMiddleware(Middleware):
    def __init__(self, logger: Logger | str = __name__):
        if isinstance(logger, str):
            logger = logging.getLogger(logger)

        self._logger: Logger = logger

    async def __call__(
        self,
        handler: HandlerType[R, RRes],
        request: R,
        *args: Any,
        **kwargs: Any,
    ) -> RRes:
        if isinstance(request, Command):
            self._logger.debug(f"Send {type(request).__name__} command", extra={"command": request})
        elif isinstance(request, Query):
            self._logger.debug(f"Make {type(request).__name__} query", extra={"query": request})
        else:
            self._logger.debug(f"Execute {type(request).__name__} request", extra={"request": request})

        res = await self._call(handler, request, *args, **kwargs)
        if isinstance(request, Command):
            self._logger.debug(f"Command {type(request).__name__} sent. Result: {res}", extra={"result": res})
        elif isinstance(request, Query):
            self._logger.debug(f"Query {type(request).__name__} made. Result: {res}", extra={"result": res})
        else:
            self._logger.debug(f"Request {type(request).__name__} executed. Result: {res}", extra={"result": res})

        return res
