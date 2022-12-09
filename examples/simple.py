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
from didiator.utils.di_builder import DiBuilder

logger = logging.getLogger(__name__)


# User entity
@dataclass
class User:
    id: int
    username: str


class UserRepo(Protocol):
    async def add_user(self, user: User) -> None:
        ...

    async def get_user_by_id(self, user_id: int) -> User:
        ...

    async def commit(self) -> None:
        ...


# Create user command and its handler
@dataclass(frozen=True)
class CreateUser(Command[int]):
    user_id: int
    username: str


class CreateUserHandler(CommandHandler[CreateUser, int]):
    def __init__(self, user_repo: UserRepo):
        self._user_repo = user_repo

    async def __call__(self, command: CreateUser) -> int:
        user = User(id=command.user_id, username=command.username)
        await self._user_repo.add_user(user)
        await self._user_repo.commit()
        return user.id


# Get user query and its handler
@dataclass(frozen=True)
class GetUserById(Query[User]):
    user_id: int


async def handle_get_user_by_id(query: GetUserById, user_repo: UserRepo) -> User:
    user = await user_repo.get_user_by_id(query.user_id)
    return user


class UserRepoImpl(UserRepo):
    def __init__(self):
        self._db_mock: dict[int, User] = {}

    async def add_user(self, user: User) -> None:
        self._db_mock[user.id] = user

    async def get_user_by_id(self, user_id: int) -> User:
        if user_id not in self._db_mock:
            raise ValueError("User with given id doesn't exist")
        return self._db_mock[user_id]

    async def commit(self) -> None:
        ...


def build_mediator(di_builder: DiBuilder) -> Mediator:
    dispatchers_middlewares = (LoggingMiddleware(level=logging.INFO), DiMiddleware(di_builder, cls_scope="request"))
    command_dispatcher = CommandDispatcherImpl(middlewares=dispatchers_middlewares)
    query_dispatcher = QueryDispatcherImpl(middlewares=dispatchers_middlewares)

    mediator = MediatorImpl(command_dispatcher, query_dispatcher)
    mediator.register_command_handler(CreateUser, CreateUserHandler)
    mediator.register_query_handler(GetUserById, handle_get_user_by_id)
    return mediator


def setup_di_builder() -> DiBuilder:
    di_scopes = ("app", "request",)
    di_builder = DiBuilder(Container(), AsyncExecutor(), di_scopes=di_scopes)
    di_builder.bind(bind_by_type(Dependent(lambda *args: di_builder, scope="app"), DiBuilder))
    di_builder.bind(bind_by_type(Dependent(build_mediator, scope="app"), Mediator))
    di_builder.bind(bind_by_type(Dependent(UserRepoImpl, scope="request"), UserRepo))
    return di_builder


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    di_builder = setup_di_builder()

    async with di_builder.enter_scope("app") as di_state:
        mediator = await di_builder.execute(Mediator, "app", state=di_state)

        async with di_builder.enter_scope("request", di_state) as di_state:
            scoped_mediator = mediator.bind(di_state=di_state)

            # It will call CreateUserHandler(UserRepoImpl()).__call__(command)
            # UserRepoImpl() created and injected automatically
            user_id = await scoped_mediator.send(CreateUser(1, "Jon"))
            logger.info(f"Created a user with id: {user_id}")

            # It will call get_user_by_id(query, user_repo)
            # UserRepoImpl created earlier will be reused in this scope
            user = await scoped_mediator.query(GetUserById(user_id))
            logger.info(f"User: {user}")


if __name__ == "__main__":
    asyncio.run(main())
