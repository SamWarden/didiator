from dataclasses import dataclass
from functools import partial

from didiator.command import Command, Handler
from didiator.middlewares.base import Middleware
from tests.mocks.middlewares import DataAdderMiddlewareMock, DataRemoverMiddlewareMock


@dataclass
class CommandMock(Command[bool]):
    pass


class HandlerMock(Handler[CommandMock, bool]):
    def __init__(self, *args, **kwargs):
        self._excluded_args = args
        self._expected_kwargs = kwargs

    async def __call__(self, command: CommandMock, *args, **kwargs) -> bool:
        assert not set(self._excluded_args) & set(kwargs)

        for key, val in self._expected_kwargs.items():
            assert kwargs[key] == val

        return True


async def mock_handle_command(command: CommandMock, *args, **kwargs) -> bool:
    assert "middleware_data" not in kwargs
    assert kwargs["additional_data"] == "data"
    return True


class TestBaseMiddleware:
    def test_init(self) -> None:
        middleware = Middleware()

        assert isinstance(middleware, Middleware)

    async def test_handling_by_middleware(self) -> None:
        middleware = Middleware()

        assert await middleware(HandlerMock, CommandMock()) is True

    async def test_handling_by_two_middlewares(self) -> None:
        middleware = Middleware()
        middleware2 = Middleware()

        assert await middleware(partial(middleware2, HandlerMock), CommandMock()) is True

    async def test_handling_by_middlewares_and_initialized_command_handler(self) -> None:
        middleware = Middleware()
        middleware2 = Middleware()

        assert await middleware(partial(middleware2, HandlerMock()), CommandMock()) is True

    async def test_handling_by_middleware_with_params(self) -> None:
        middleware = DataAdderMiddlewareMock(additional_data="data")

        assert await middleware(HandlerMock(additional_data="data"), CommandMock()) is True

    async def test_handling_by_two_middlewares_with_params(self) -> None:
        middleware = DataAdderMiddlewareMock(additional_data="data", some_data="value")
        middleware2 = DataRemoverMiddlewareMock("middleware_data")

        assert await middleware(
            partial(middleware2, HandlerMock("middleware_data", additional_data="data", some_data="value")),
            CommandMock(),
            middleware_data="data",
        ) is True

    async def test_handling_with_middlewares_and_function_command_handler(self) -> None:
        middleware = DataAdderMiddlewareMock(additional_data="data")
        middleware2 = DataRemoverMiddlewareMock("middleware_data")

        assert await middleware(partial(middleware2, mock_handle_command), CommandMock(), middleware_data="data") is True
