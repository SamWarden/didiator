from didiator.interface import Request


class MediatorError(Exception):
    pass


class HandlerNotFound(MediatorError, TypeError):
    request: Request

    def __init__(self, text: str, request: Request):
        super().__init__(text)
        self.request = request


class CommandHandlerNotFound(HandlerNotFound):
    pass


class QueryHandlerNotFound(HandlerNotFound):
    pass
