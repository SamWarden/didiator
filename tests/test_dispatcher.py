from dataclasses import dataclass

from didiator.implementation.command import Command, CommandHandler

from didiator.implementation.dispatcher import CommandDispatcherImpl
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


class CreateUserHandler(CommandHandler[CreateUserCommand, int]):
    # def __init__(self, uow: UnitOfWork):
    #     self._uow = uow
    #

    async def __call__(self, command: CreateUserCommand) -> int:
        return command.user_id
    #     user = User(command.user_id, command.username)
    #     self._uow.user.add_user(user)
    #     return user.user_id


class ExtendedCreateUserHandler(CommandHandler[CreateUserCommand, UserId]):
    async def __call__(self, command: CreateUserCommand) -> UserId:
        return UserId(command.user_id)


class UpdateUserHandler(CommandHandler[UpdateUserCommand, str]):
    # def __init__(self, uow: UnitOfWork):
    #     self._uow = uow
    #

    async def __call__(self, command: int, additional_data: str = "") -> str:
        return additional_data


class TestCommandDispatcher:
    async def test_init(self) -> None:
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
