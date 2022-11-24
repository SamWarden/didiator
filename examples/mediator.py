import asyncio
from dataclasses import dataclass
from typing import Protocol
import logging

from di.container import bind_by_type, Container
from di.dependent import Dependent
from di.executors import AsyncExecutor

from didiator import Command, CommandHandler, Mediator, Query, QueryDispatcherImpl, QueryHandler
from didiator.dispatchers.command import CommandDispatcherImpl
from didiator.mediator import MediatorImpl
from didiator.middlewares.di import DiMiddleware
from didiator.middlewares.logging import LoggingMiddleware

logger = logging.getLogger(__name__)


# User entity
@dataclass
class User:
    user_id: int
    username: str


# Protocols
class Session(Protocol):
    async def commit(self) -> None:
        ...


class UserRepo(Protocol):
    def add_user(self, user: User) -> None:
        ...

    async def get_user_by_id(self, user_id: int) -> User:
        ...


class UnitOfWork(Protocol):
    user: UserRepo

    async def commit(self) -> None:
        ...


# Create use command and its handler
@dataclass(frozen=True)
class CreateUser(Command[int]):
    user_id: int
    username: str


class CreateUserHandler(CommandHandler[CreateUser, int]):
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def __call__(self, command: CreateUser) -> int:
        user = User(command.user_id, command.username)
        self._uow.user.add_user(user)
        return user.user_id


# Get user query and its handler
@dataclass(frozen=True)
class GetUserById(Query[User]):
    user_id: int


class GetUserByIdHandler(QueryHandler[GetUserById, User]):
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def __call__(self, query: GetUserById) -> User:
        return await self._uow.user.get_user_by_id(query.user_id)


# Protocol implementations
class UnitOfWorkImpl:
    def __init__(self, session: Session, user_repo: UserRepo):
        self._session = session
        self.user = user_repo

    async def commit(self) -> None:
        await self._session.commit()


class SessionMock:
    async def commit(self) -> None:
        """A standard commit method mock"""
        pass


class UserRepoMock:
    def __init__(self, session: Session):
        self._session = session
        self._db_mock: dict[int, User] = {}

    def add_user(self, user: User) -> None:
        self._db_mock[user.user_id] = user

    async def get_user_by_id(self, user_id: int) -> User:
        if user_id not in self._db_mock:
            raise ValueError("User with given id doesn't exist")
        return self._db_mock[user_id]


# Generic code of controller with using Mediator
class UserController:
    def __init__(self, mediator: Mediator):
        self._mediator = mediator

    async def interact_with_user(self) -> None:
        user_id = await self._mediator.send(CreateUser(1, "Jon"))
        logger.info(f"Created a user with id: {user_id}")
        user = await self._mediator.query(GetUserById(user_id))
        logger.info(f"User: {user}")


async def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    di_container = Container()
    di_executor = AsyncExecutor()

    di_container.bind(bind_by_type(Dependent(UnitOfWorkImpl, scope="request"), UnitOfWork))
    di_container.bind(bind_by_type(Dependent(UserRepoMock, scope="request"), UserRepo))
    di_container.bind(bind_by_type(Dependent(SessionMock, scope="request"), Session))

    command_dispatcher = CommandDispatcherImpl(middlewares=(LoggingMiddleware(), DiMiddleware(di_container, di_executor, ("request",), cls_scope="request")))
    query_dispatcher = QueryDispatcherImpl(middlewares=(LoggingMiddleware(), DiMiddleware(di_container, di_executor, ("request",), cls_scope="request")))

    command_dispatcher.register_handler(CreateUser, CreateUserHandler)
    query_dispatcher.register_handler(GetUserById, GetUserByIdHandler)

    initialized_mediator = MediatorImpl(command_dispatcher, query_dispatcher)
    async with di_container.enter_scope("request") as di_state:
        scoped_mediator = initialized_mediator.bind(di_state=di_state)
        # mediator = MediatorImpl(command_dispatcher, query_dispatcher, extra_data={"di_state": di_state})

        user_controller = UserController(scoped_mediator)
        await user_controller.interact_with_user()


if __name__ == "__main__":
    asyncio.run(main())
