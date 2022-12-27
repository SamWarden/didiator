import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Protocol
import logging

from di.container import bind_by_type, Container, ContainerState
from di.dependent import Dependent, Marker
from di.executors import AsyncExecutor

from didiator import Command, CommandHandler, Mediator, Query, QueryDispatcherImpl, Event, EventHandler, EventObserverImpl
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


class UserApiClient(Protocol):
    async def get_user_by_id(self, user_id: int) -> User:
        ...


# Create user command and its handler
@dataclass(frozen=True)
class CreateUser(Command[int]):
    user_id: int
    username: str


class CreateUserHandler(CommandHandler[CreateUser, int]):
    def __init__(self, user_repo: UserRepo, mediator: Mediator, user_api: UserApiClient) -> None:
        logger.info("Init CreateUserHandler: %s, %s", mediator, user_api)
        self._user_repo = user_repo
        self._mediator = mediator
        self._user_api = user_api

    async def __call__(self, command: CreateUser) -> int:
        user = User(id=command.user_id, username=command.username)
        await self._user_repo.add_user(user)
        logger.info("User added: %s", user)
        await self._mediator.publish(UserCreated(user.id))
        logger.info("UserCreated published: %s", user)
        await self._user_repo.commit()
        # It has to return None because it will have its own context with another in-memory UserRepoImpl
        logger.info("Get user from another context: %s", await self._user_api.get_user_by_id(user.id))
        return user.id


# Get user query and its handler
@dataclass(frozen=True)
class GetUserById(Query[User]):
    user_id: int


async def handle_get_user_by_id(query: GetUserById, user_repo: UserRepo) -> User:
    user = await user_repo.get_user_by_id(query.user_id)
    return user


# Define UserCreated event and its handler
@dataclass(frozen=True)
class UserCreated(Event):
    user_id: int


class UserCreatedHandler(EventHandler[UserCreated]):
    def __init__(self, user_repo: UserRepo):
        self._user_repo = user_repo

    async def __call__(self, event: UserCreated) -> None:
        user = await self._user_repo.get_user_by_id(event.user_id)
        logger.info("User created handler: %s", user)


class UserRepoImpl(UserRepo):
    def __init__(self):
        logger.info("Init UserRepo")
        self._db_mock: dict[int, User] = {}

    async def add_user(self, user: User) -> None:
        self._db_mock[user.id] = user

    async def get_user_by_id(self, user_id: int) -> User:
        if user_id not in self._db_mock:
            raise ValueError("User with given id doesn't exist")
        return self._db_mock[user_id]

    async def commit(self) -> None:
        ...


# def build_di_state() -> ContainerState:
#     return ContainerState()


class AppContainerState(ContainerState):
    pass


class UserApiInMemoryClient(UserApiClient):
    def __init__(
        self, mediator: Mediator, di_builder: DiBuilder,
        di_state: AppContainerState, #Annotated[AppContainerState, Marker(use_cache=False, scope="app")],
    ):
        logger.info("Init UserApiClient: %s", di_state.stacks)
        self._mediator = mediator
        self._di_builder = di_builder
        self._di_state = di_state

    async def get_user_by_id(self, user_id: int) -> User | None:
        async with self._di_builder.enter_scope("request", self._di_state) as di_state:
            try:
                return await self._mediator.query(GetUserById(user_id), di_state=di_state)
            except ValueError:
                return None


def build_mediator(di_builder: DiBuilder) -> Mediator:
    middlewares = (LoggingMiddleware(level=logging.INFO), DiMiddleware(di_builder, cls_scope="request"))
    command_dispatcher = CommandDispatcherImpl(middlewares=middlewares)
    query_dispatcher = QueryDispatcherImpl(middlewares=middlewares)
    event_observer = EventObserverImpl(middlewares=middlewares)

    mediator = MediatorImpl(command_dispatcher, query_dispatcher, event_observer)
    mediator.register_command_handler(CreateUser, CreateUserHandler)
    mediator.register_query_handler(GetUserById, handle_get_user_by_id)
    mediator.register_event_handler(UserCreated, UserCreatedHandler)
    return mediator


def create_mediator_builder(mediator: Mediator) -> Callable[[ContainerState], Mediator]:
    def _build_mediator(di_state: ContainerState) -> Mediator:
        logger.info("Build new mediator: with di_state=%s", di_state.stacks)
        return mediator.bind(di_state=di_state)
    return _build_mediator


def setup_di_builder() -> DiBuilder:
    di_scopes = ("app", "request",)
    di_builder = DiBuilder(Container(), AsyncExecutor(), di_scopes=di_scopes)
    di_builder.bind(bind_by_type(Dependent(lambda *args: di_builder, scope="app"), DiBuilder))
    di_builder.bind(bind_by_type(Dependent(build_mediator, scope="app"), Mediator))
    di_builder.bind(bind_by_type(Dependent(UserApiInMemoryClient, scope="request"), UserApiClient))
    di_builder.bind(bind_by_type(Dependent(UserRepoImpl, scope="request"), UserRepo))
    return di_builder


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    di_builder = setup_di_builder()

    async with di_builder.enter_scope("app") as di_state:
        # di_builder.bind(bind_by_type(Dependent(lambda *args: di_state, scope="request", use_cache=False), ContainerState))
        di_builder.bind(bind_by_type(Dependent(lambda *args: di_state, scope="app"), AppContainerState))

        mediator = await di_builder.execute(Mediator, "app", state=di_state)
        di_builder.bind(bind_by_type(Dependent(create_mediator_builder(mediator), scope="request"), Mediator))

        async with di_builder.enter_scope("request", di_state) as di_state2:
            logger.info("Enter main request scope")
            scoped_mediator = mediator.bind(di_state=di_state2)

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
