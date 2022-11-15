import pytest

from didiator.dispatcher import CommandDispatcherImpl


@pytest.fixture()
def command_dispatcher() -> CommandDispatcherImpl:
    command_dispatcher = CommandDispatcherImpl()
    return command_dispatcher
