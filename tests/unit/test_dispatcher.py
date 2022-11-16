from dataclasses import dataclass

from didiator.command import Command, RequestHandler

from didiator.command_dispatcher import CommandDispatcherImpl
from tests.mocks.middlewares import DataAdderMiddlewareMock, DataRemoverMiddlewareMock


@dataclass
class CreateUserCommand(Command[int]):
    user_id: int
    username: str


@dataclass
class UpdateUserCommand(Command[str]):
    user_id: int
    username: str


class NotCommand:
    pass


class UserId(int):
    pass


class CreateUserHandler(RequestHandler[CreateUserCommand, int]):
    async def __call__(self, command: CreateUserCommand) -> int:
        return command.user_id


class ExtendedCreateUserHandler(RequestHandler[CreateUserCommand, UserId]):
    async def __call__(self, command: CreateUserCommand) -> UserId:
        return UserId(command.user_id)


class UpdateUserHandler(RequestHandler[UpdateUserCommand, str]):
    async def __call__(self, command: UpdateUserCommand, additional_data: str = "") -> str:
        return additional_data


async def handle_update_user(command: UpdateUserCommand, additional_data: str = "") -> str:
    return additional_data


class TestCommandDispatcher:
    def test_init(self) -> None:
        command_dispatcher: CommandDispatcherImpl = CommandDispatcherImpl()

        assert isinstance(command_dispatcher, CommandDispatcherImpl)
        assert command_dispatcher.handlers == {}
        assert command_dispatcher.middlewares == ()

    async def test_command_handler_registration(self, command_dispatcher: CommandDispatcherImpl) -> None:
        command_dispatcher.register_handler(CreateUserCommand, CreateUserHandler)
        assert command_dispatcher.handlers == {CreateUserCommand: CreateUserHandler}

        command_dispatcher.register_handler(UpdateUserCommand, UpdateUserHandler)
        assert command_dispatcher.handlers == {CreateUserCommand: CreateUserHandler, UpdateUserCommand: UpdateUserHandler}

        command_dispatcher.register_handler(CreateUserCommand, ExtendedCreateUserHandler)
        assert command_dispatcher.handlers == {CreateUserCommand: ExtendedCreateUserHandler, UpdateUserCommand: UpdateUserHandler}

    async def test_initialization_with_middlewares(self) -> None:
        middleware1 = DataAdderMiddlewareMock()
        command_dispatcher = CommandDispatcherImpl(middlewares=(middleware1,))
        assert command_dispatcher.middlewares == (middleware1,)

        middleware2 = DataRemoverMiddlewareMock()
        command_dispatcher = CommandDispatcherImpl(middlewares=[middleware1, middleware2])
        assert command_dispatcher.middlewares == (middleware1, middleware2)

    async def test_command_sending(self, command_dispatcher: CommandDispatcherImpl) -> None:
        command_dispatcher.register_handler(CreateUserCommand, CreateUserHandler)

        res = await command_dispatcher.send(CreateUserCommand(1, "Jon"))
        assert res == 1

    async def test_command_sending_with_middlewares(self) -> None:
        middleware1 = DataAdderMiddlewareMock(middleware_data="data", additional_data="value")
        middleware2 = DataRemoverMiddlewareMock("middleware_data")
        command_dispatcher = CommandDispatcherImpl(middlewares=[middleware1, middleware2])

        command_dispatcher.register_handler(UpdateUserCommand, UpdateUserHandler)

        res = await command_dispatcher.send(UpdateUserCommand(1, "Sam"))
        assert res == "value"

    async def test_command_sending_with_function_handler(self) -> None:
        command_dispatcher = CommandDispatcherImpl()
        command_dispatcher.register_handler(UpdateUserCommand, handle_update_user)

        res = await command_dispatcher.send(UpdateUserCommand(1, "Sam"), additional_data="value")
        assert res == "value"

    async def test_command_sending_with_middlewares_and_function_handler(self) -> None:
        middleware1 = DataAdderMiddlewareMock(middleware_data="data", additional_data="value")
        middleware2 = DataRemoverMiddlewareMock("middleware_data")
        command_dispatcher = CommandDispatcherImpl(middlewares=[middleware1, middleware2])

        command_dispatcher.register_handler(UpdateUserCommand, handle_update_user)

        res = await command_dispatcher.send(UpdateUserCommand(1, "Sam"))
        assert res == "value"
