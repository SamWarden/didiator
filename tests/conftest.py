import pytest

from didiator.command_dispatcher import CommandDispatcherImpl
from didiator.query_dispatcher import QueryDispatcherImpl


@pytest.fixture()
def command_dispatcher() -> CommandDispatcherImpl:
    command_dispatcher = CommandDispatcherImpl()
    return command_dispatcher


@pytest.fixture()
def query_dispatcher() -> QueryDispatcherImpl:
    query_dispatcher = QueryDispatcherImpl()
    return query_dispatcher
