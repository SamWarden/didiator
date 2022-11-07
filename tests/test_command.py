from typing import Awaitable, Callable, Protocol, TypeVar

import pytest

from didiator.implementation.command import Command, CommandDispatcherImpl, CommandHandler


class CreateUserCommand(Command[int]):
    user_id: int
    username: str


class UpdateUserCommand(Command[None]):
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

    async def handle(self, command: CreateUserCommand) -> int:
        return command.user_id
    #     user = User(command.user_id, command.username)
    #     self._uow.user.add_user(user)
    #     return user.user_id


class ExtendedCreateUserHandler(CommandHandler[CreateUserCommand, UserId]):
    async def handle(self, command: CreateUserCommand) -> UserId:
        return UserId(command.user_id)


class UpdateUserHandler(CommandHandler[UpdateUserCommand, None]):
    # def __init__(self, uow: UnitOfWork):
    #     self._uow = uow
    #

    async def handle(self, command: UpdateUserCommand) -> None:
        return None


CR = TypeVar("CR")


class CommandResult(Protocol):
    pass


C = TypeVar("C", bound=Command[CommandResult])


class MockMiddleware:
    # def __init__(self, ):
    async def __call__(self, handler: Callable[[C, ...], Awaitable[CR]], command: C, *args, **kwargs) -> CR:
        return await handler(command, *args, **kwargs)


class TestCommandDispatcher:
    @pytest.mark.asyncio
    async def test_init(self) -> None:
        command_dispatcher: CommandDispatcherImpl = CommandDispatcherImpl()

        assert isinstance(command_dispatcher, CommandDispatcherImpl)
        assert command_dispatcher.handlers == {}
        assert command_dispatcher.middlewares == ()

    @pytest.mark.asyncio
    async def test_command_handler_registration(self, command_dispatcher: CommandDispatcherImpl) -> None:
        command_dispatcher.register_handler(CreateUserCommand, CreateUserHandler)
        assert command_dispatcher.handlers == {CreateUserCommand: CreateUserHandler}

        command_dispatcher.register_handler(UpdateUserCommand, UpdateUserHandler)
        assert command_dispatcher.handlers == {CreateUserCommand: CreateUserHandler, UpdateUserCommand: UpdateUserHandler}

        command_dispatcher.register_handler(CreateUserCommand, ExtendedCreateUserHandler)
        assert command_dispatcher.handlers == {CreateUserCommand: ExtendedCreateUserHandler, UpdateUserCommand: UpdateUserHandler}

    @pytest.mark.asyncio
    async def test_initialization_with_middlewares(self) -> None:
        middleware1 = MockMiddleware()
        command_dispatcher = CommandDispatcherImpl(middlewares=(middleware1,))
        assert command_dispatcher.middlewares == (middleware1,)

        middleware2 = MockMiddleware()
        command_dispatcher = CommandDispatcherImpl(middlewares=[middleware1, middleware2])
        assert command_dispatcher.middlewares == (middleware1, middleware2)
