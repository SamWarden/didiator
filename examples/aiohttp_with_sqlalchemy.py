import asyncio
import json
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from typing import Awaitable, Protocol
import logging
from uuid import UUID, uuid4

from aiohttp import web
from aiohttp.web_request import Request, StreamResponse
from di import bind_by_type, Container, ScopeState
from di.dependent import Dependent
from di.executors import AsyncExecutor
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from didiator import (
    Command, CommandHandler, Event, EventObserverImpl, Mediator, Query, QueryDispatcherImpl,
    QueryHandler,
)
from didiator.dispatchers.command import CommandDispatcherImpl
from didiator.interface.handlers.event import EventHandler
from didiator.interface.utils.di_builder import DiBuilder
from didiator.mediator import MediatorImpl
from didiator.middlewares.di import DiMiddleware, DiScopes
from didiator.middlewares.logging import LoggingMiddleware
from didiator.utils.di_builder import DiBuilderImpl

logger = logging.getLogger(__name__)

# This is an example of usage didiator with DI, aiogram, and SQLAlchemy.
# To run this script, install them by running this command:
# pip install -U aiohttp SQLAlchemy DI
# and set the value of TG_BOT_TOKEN to your token


# User entity
@dataclass
class User:
    id: UUID
    username: str


class UserRepo(Protocol):
    def add_user(self, user: User) -> None:
        ...

    async def get_user_by_id(self, user_id: UUID) -> User:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...


class TgUpdate:
    update_id: UUID


# User created event and its handler
@dataclass(frozen=True)
class UserCreated(Event):
    user_id: UUID
    username: str


class UserCreatedHandler(EventHandler[UserCreated]):
    def __init__(self, update: TgUpdate):
        self._update = update

    async def __call__(self, event: UserCreated) -> None:
        logger.info("User registered")


# Create user command and its handler
@dataclass(frozen=True)
class CreateUser(Command[int]):
    username: str


class UserAlreadyExists(RuntimeError):
    pass


class CreateUserHandler(CommandHandler[CreateUser, UUID]):
    def __init__(self, mediator: Mediator, user_repo: UserRepo):
        self._mediator = mediator
        self._user_repo = user_repo

    async def __call__(self, command: CreateUser) -> UUID:
        user = User(id=uuid4(), username=command.username)
        self._user_repo.add_user(user)
        await self._mediator.publish(UserCreated(user.id, user.username))

        try:
            await self._user_repo.commit()
        except IntegrityError:
            await self._user_repo.rollback()
            raise UserAlreadyExists

        return user.id


# Get user query and its handler
@dataclass(frozen=True)
class GetUserById(Query[User]):
    user_id: UUID


class GetUserByIdHandler(QueryHandler[GetUserById, User]):
    def __init__(self, user_repo: UserRepo) -> None:
        self._user_repo = user_repo

    async def __call__(self, query) -> User:
        user = await self._user_repo.get_user_by_id(query.user_id)
        return user


# SQLAlchemy declaration

class BaseModel(DeclarativeBase):
    pass


class UserModel(BaseModel):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)


class UserRepoImpl(UserRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    def add_user(self, user: User) -> None:
        self._session.add(UserModel(id=user.id, username=user.username))

    async def get_user_by_id(self, user_id: UUID) -> User:
        user_model = await self._session.get(UserModel, user_id)
        return User(user_model.id, user_model.username)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


@dataclass(frozen=True)
class Config:
    db_uri: str


def build_config() -> Config:
    return Config(
        db_uri="sqlite+aiosqlite://",
    )


async def build_sa_engine(config: Config) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(config.db_uri, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield engine

    await engine.dispose()


def build_sa_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


async def build_sa_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


def build_mediator(di_builder: DiBuilder) -> Mediator:
    middlewares = (LoggingMiddleware(level=logging.INFO), DiMiddleware(di_builder, scopes=DiScopes("request")))
    command_dispatcher = CommandDispatcherImpl(middlewares=middlewares)
    query_dispatcher = QueryDispatcherImpl(middlewares=middlewares)
    event_observer = EventObserverImpl(middlewares=middlewares)

    mediator = MediatorImpl(command_dispatcher, query_dispatcher, event_observer)
    mediator.register_command_handler(CreateUser, CreateUserHandler)
    mediator.register_query_handler(GetUserById, GetUserByIdHandler)
    mediator.register_event_handler(UserCreated, UserCreatedHandler)

    return mediator


def get_mediator_builder(mediator: Mediator):
    def _build_mediator(di_state: ScopeState) -> Mediator:
        return mediator.bind(di_state=di_state)
    return _build_mediator


def setup_di_builder() -> DiBuilderImpl:
    di_container = Container()
    di_executor = AsyncExecutor()
    di_scopes = ["app", "request"]
    di_builder = DiBuilderImpl(di_container, di_executor, di_scopes=di_scopes)

    di_builder.bind(bind_by_type(Dependent(lambda *args: di_builder, scope="app"), DiBuilder))
    di_builder.bind(bind_by_type(Dependent(build_config, scope="app"), Config))
    di_builder.bind(bind_by_type(Dependent(build_sa_engine, scope="app"), AsyncEngine))
    di_builder.bind(bind_by_type(Dependent(build_sa_session_factory, scope="app"), async_sessionmaker[AsyncSession]))
    di_builder.bind(bind_by_type(Dependent(build_sa_session, scope="request"), AsyncSession))
    di_builder.bind(bind_by_type(Dependent(UserRepoImpl, scope="request"), UserRepo))
    return di_builder


Controller = Callable[..., Awaitable[StreamResponse]]


@web.middleware
class DiWebMiddleware:
    def __init__(
        self, di_builder: DiBuilder, di_state: ScopeState | None = None,
    ) -> None:
        self._di_builder = di_builder
        self._di_state = di_state

    async def __call__(
        self,
        request: Request,
        handler: Controller,
    ) -> Awaitable[StreamResponse]:
        async with self._di_builder.enter_scope("request", self._di_state) as di_state:
            return await self._di_builder.execute(handler, "request", state=di_state, values={
                Request: request, ScopeState: di_state,
            })


async def create_user_handler(request: Request, mediator: Mediator) -> web.Response:
    logger.info("Request received: %s", request)
    data = await request.json()
    username = data.get("username")
    if not isinstance(username, str):
        return web.Response(status=400, text="Body has to contain username")

    try:
        # It will call CreateUserHandler(UserRepoImpl()).__call__(command)
        # UserRepoImpl() created and injected automatically
        user_id = await mediator.send(CreateUser(username))
    except UserAlreadyExists:
        logger.info("User already exists")
        return web.Response(status=409, text="Username already exist")

    # It will call GetUserByIdHandler(user_repo).__call__(query)
    # UserRepoImpl created earlier will be reused in this scope
    user = await mediator.query(GetUserById(user_id))
    return web.Response(status=201, text=json.dumps(({"user_id": str(user.id), "username": user.username})))


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    di_builder = setup_di_builder()

    async with di_builder.enter_scope("app") as di_state:
        mediator = await di_builder.execute(build_mediator, "app", state=di_state)
        di_builder.bind(bind_by_type(Dependent(get_mediator_builder(mediator), scope="request"), Mediator))

        app = web.Application(middlewares=(DiWebMiddleware(di_builder, di_state),))
        app.add_routes([web.route("POST", "/users/", create_user_handler)])

        await web._run_app(app, host="127.0.0.1", port=5000)  # noqa


if __name__ == "__main__":
    asyncio.run(main())
