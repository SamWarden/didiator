import pytest

from didiator.dispatchers.command import CommandDispatcherImpl
from didiator.dispatchers.query import QueryDispatcherImpl


@pytest.fixture()
def command_dispatcher() -> CommandDispatcherImpl:
    command_dispatcher = CommandDispatcherImpl()
    return command_dispatcher


@pytest.fixture()
def query_dispatcher() -> QueryDispatcherImpl:
    query_dispatcher = QueryDispatcherImpl()
    return query_dispatcher
