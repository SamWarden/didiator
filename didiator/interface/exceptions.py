
class HandlerNotFound(TypeError):
    ...


class CommandHandlerNotFound(HandlerNotFound):
    ...


class QueryHandlerNotFound(HandlerNotFound):
    ...
