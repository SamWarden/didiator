import abc

from didiator.interface.entities.request import Request


class Event(Request[None], abc.ABC):
    pass
