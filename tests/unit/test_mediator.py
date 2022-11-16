from dataclasses import dataclass

from didiator.command import Command, CommandHandler
from didiator.command_dispatcher import CommandDispatcherImpl
from didiator.interface.mediator import CommandMediator, Mediator, QueryMediator
from didiator.mediator import MediatorImpl
from didiator.query import Query, QueryHandler
from didiator.query_dispatcher import QueryDispatcherImpl
from tests.mocks.middlewares import DataRemoverMiddlewareMock


@dataclass
class CommandMock(Command[str]):
    result: str


@dataclass
class QueryMock(Query[str]):
    result: str


class CommandHandlerMock(CommandHandler[CommandMock, str]):
    def __init__(self, *args, **kwargs):
        self._excluded_args = args
        self._expected_kwargs = kwargs

    async def __call__(self, command: CommandMock, *args, **kwargs) -> str:
        assert not set(self._excluded_args) & set(kwargs)

        for key, val in self._expected_kwargs.items():
            assert kwargs[key] == val

        return command.result


class QueryHandlerMock(QueryHandler[QueryMock, str]):
    def __init__(self, *args, **kwargs):
        self._excluded_args = args
        self._expected_kwargs = kwargs

    async def __call__(self, query: QueryMock, *args, **kwargs) -> str:
        assert not set(self._excluded_args) & set(kwargs)

        for key, val in self._expected_kwargs.items():
            assert kwargs[key] == val

        return query.result


class TestMediator:
    def test_init(self) -> None:
        mediator: Mediator = MediatorImpl()

        assert isinstance(mediator, MediatorImpl)
        assert isinstance(MediatorImpl(CommandDispatcherImpl(), QueryDispatcherImpl()), MediatorImpl)
        assert isinstance(MediatorImpl(CommandDispatcherImpl()), MediatorImpl)
        assert isinstance(MediatorImpl(
            command_dispatcher=CommandDispatcherImpl(), query_dispatcher=QueryDispatcherImpl(),
        ), MediatorImpl)

    async def test_sending_command_through_mediator(self) -> None:
        command_dispatcher = CommandDispatcherImpl()
        command_dispatcher.register_handler(CommandMock, CommandHandlerMock)

        mediator: CommandMediator = MediatorImpl(command_dispatcher)

        assert await mediator.send(CommandMock("data")) == "data"

    async def test_query_queries_through_mediator(self) -> None:
        query_dispatcher = QueryDispatcherImpl()
        query_dispatcher.register_handler(QueryMock, CommandHandlerMock)

        mediator: QueryMediator = MediatorImpl(query_dispatcher=query_dispatcher)

        assert await mediator.query(QueryMock("data")) == "data"

    async def test_sending_command_through_mediator_with_extra_args(self) -> None:
        command_dispatcher = CommandDispatcherImpl((DataRemoverMiddlewareMock("middleware_data"),))
        command_dispatcher.register_handler(CommandMock, CommandHandlerMock(additional_data="arg"))

        mediator = MediatorImpl(command_dispatcher)

        assert await mediator.send(CommandMock("data"), middleware_data="value", additional_data="arg") == "data"

    async def test_extra_data_binding(self) -> None:
        mediator_without_extra_data = MediatorImpl()
        assert mediator_without_extra_data.extra_data == {}

        mediator = MediatorImpl(extra_data={"additional_data": "arg"})
        assert mediator.extra_data == {"additional_data": "arg"}

        mediator2 = mediator.bind(middleware_data="value", some_data=1)
        assert mediator.extra_data == {"additional_data": "arg"}
        assert mediator2.extra_data == {"additional_data": "arg", "middleware_data": "value", "some_data": 1}

        mediator3 = mediator2.unbind("some_data", "additional_data")
        assert mediator.extra_data == {"additional_data": "arg"}
        assert mediator2.extra_data == {"additional_data": "arg", "middleware_data": "value", "some_data": 1}
        assert mediator3.extra_data == {"middleware_data": "value"}

        mediator4 = mediator2.bind(another_data=None, some_data=2)
        assert mediator.extra_data == {"additional_data": "arg"}
        assert mediator2.extra_data == {"additional_data": "arg", "middleware_data": "value", "some_data": 1}
        assert mediator3.extra_data == {"middleware_data": "value"}
        assert mediator4.extra_data == {
            "additional_data": "arg", "middleware_data": "value", "some_data": 2, "another_data": None,
        }

    async def test_sending_command_through_mediator_with_extra_data(self) -> None:
        command_dispatcher = CommandDispatcherImpl()
        command_dispatcher.register_handler(CommandMock, CommandHandlerMock(additional_data="arg"))

        mediator = MediatorImpl(command_dispatcher, extra_data={"additional_data": "arg"})
        mediator2 = mediator.bind(middleware_data="value")
        assert await mediator2.send(CommandMock("data")) == "data"
