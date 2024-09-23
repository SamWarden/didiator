from typing import Any

from didiator.interface.entities import Request


class MediatorError(Exception):
    pass


class HandlerNotFound(MediatorError, TypeError):
    request: Request[Any]

    def __init__(self, text: str, request: Request[Any]):
        super().__init__(text)
        self.request = request
