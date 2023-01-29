import asyncio
import os
from collections.abc import AsyncGenerator, Callable
from dataclasses import dataclass
from typing import Any, Awaitable, Protocol
import logging

import aiogram
import aiogram.filters
import aiogram.types as tg
from di import bind_by_type, Container, ScopeState
from di.dependent import Dependent
from di.executors import AsyncExecutor
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, sessionmaker

from didiator import Command, CommandHandler, Event, EventObserverImpl, Mediator, Query, QueryDispatcherImpl
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
# pip install -U --pre aiogram SQLAlchemy DI
# and set the value of TG_BOT_TOKEN to your token

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")

# SQLAlchemy declaration
BaseModel = declarative_base()


# User entity
@dataclass
class User:
    id: int
    username: str


class UserRepo(Protocol):
    def add_user(self, user: User) -> None:
        ...

    async def get_user_by_id(self, user_id: int) -> User:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...


# User created event and its handler
@dataclass(frozen=True)
class UserCreated(Event):
    user_id: int
    username: str


class UserCreatedHandler(EventHandler[UserCreated]):
    def __init__(self, bot: aiogram.Bot):
        self._bot = bot

    async def __call__(self, event: UserCreated) -> None:
        logger.info("User registered, %s", self._bot)
        await self._bot.send_message(event.user_id, f"{event.username}, you're registered")


# Create user command and its handler
@dataclass(frozen=True)
class CreateUser(Command[int]):
    user_id: int
    username: str


class UserAlreadyExists(RuntimeError):
    pass


class CreateUserHandler(CommandHandler[CreateUser, int]):
    def __init__(self, mediator: Mediator, user_repo: UserRepo):
        self._mediator = mediator
        self._user_repo = user_repo

    async def __call__(self, command: CreateUser) -> int:
        user = User(id=command.user_id, username=command.username)
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
    user_id: int


async def handle_get_user_by_id(query: GetUserById, user_repo: UserRepo) -> User:
    user = await user_repo.get_user_by_id(query.user_id)
    return user


class UserModel(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    username: Mapped[str]


class UserRepoImpl(UserRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    def add_user(self, user: User) -> None:
        self._session.add(UserModel(id=user.id, username=user.username))

    async def get_user_by_id(self, user_id: int) -> User:
        user_model = await self._session.get(UserModel, user_id)
        return User(user_model.id, user_model.username)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


@dataclass(frozen=True)
class Config:
    db_uri: str
    bot_token: str


def build_config() -> Config:
    return Config(
        db_uri="sqlite+aiosqlite://",
        bot_token=TG_BOT_TOKEN,
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


def build_repo(session: AsyncSession) -> UserRepoImpl:
    return UserRepoImpl(session)


def build_tg_bot(config: Config) -> aiogram.Bot:
    return aiogram.Bot(config.bot_token)


def build_tg_dispatcher() -> aiogram.Dispatcher:
    return aiogram.Dispatcher()


def build_mediator(di_builder: DiBuilder) -> Mediator:
    # middlewares = (LoggingMiddleware(level=logging.INFO), DiMiddleware(di_builder, scope="tg_update"))
    middlewares = (LoggingMiddleware(level=logging.INFO), DiMiddleware(di_builder, scopes=DiScopes("tg_update")))
    command_dispatcher = CommandDispatcherImpl(middlewares=middlewares)
    query_dispatcher = QueryDispatcherImpl(middlewares=middlewares)
    event_observer = EventObserverImpl(middlewares=middlewares)

    mediator = MediatorImpl(command_dispatcher, query_dispatcher, event_observer)
    mediator.register_command_handler(CreateUser, CreateUserHandler)
    mediator.register_query_handler(GetUserById, handle_get_user_by_id)
    mediator.register_event_handler(UserCreated, UserCreatedHandler)

    return mediator


def setup_di_builder() -> DiBuilderImpl:
    di_container = Container()
    di_executor = AsyncExecutor()
    di_scopes = ["app", "tg_update"]
    di_builder = DiBuilderImpl(di_container, di_executor, di_scopes=di_scopes)

    di_builder.bind(bind_by_type(Dependent(lambda *args: di_builder, scope="app"), DiBuilder))
    di_builder.bind(bind_by_type(Dependent(build_config, scope="app"), Config))
    di_builder.bind(bind_by_type(Dependent(build_mediator, scope="app"), Mediator))
    di_builder.bind(bind_by_type(Dependent(build_tg_bot, scope="app"), aiogram.Bot))
    di_builder.bind(bind_by_type(Dependent(build_sa_engine, scope="app"), AsyncEngine))
    di_builder.bind(bind_by_type(Dependent(build_sa_session_factory, scope="app"), async_sessionmaker[AsyncSession]))
    di_builder.bind(bind_by_type(Dependent(build_sa_session, scope="tg_update"), AsyncSession))
    di_builder.bind(bind_by_type(Dependent(build_repo, scope="tg_update"), UserRepo))
    return di_builder


def create_mediator_builder(mediator: Mediator) -> Callable[[ScopeState], Mediator]:
    def _build_mediator(di_state: ScopeState) -> Mediator:
        return mediator.bind(di_state=di_state)
    return _build_mediator


class MediatorMiddleware(aiogram.BaseMiddleware):
    def __init__(
        self, mediator: Mediator, di_builder: DiBuilder, di_state: ScopeState | None = None,
    ) -> None:
        self._mediator = mediator
        self._di_builder = di_builder
        self._di_state = di_state

    async def __call__(
        self,
        handler: Callable[[tg.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: tg.TelegramObject,
        data: dict[str, Any],
    ) -> None:
        async with self._di_builder.enter_scope("tg_update", self._di_state) as di_state:
            mediator = self._mediator.bind(di_state=di_state)
            data["mediator"] = mediator
            result = await handler(event, data)
            del data["mediator"]
        return result


async def echo_handler(message: tg.Message, mediator: Mediator) -> None:
    logger.info(f"Message received: message_id={message.message_id}, text={message.text}")
    try:
        # It will call CreateUserHandler(UserRepoImpl()).__call__(command)
        # UserRepoImpl() created and injected automatically
        await mediator.send(CreateUser(message.from_user.id, message.from_user.username))
    except UserAlreadyExists:
        logger.info("User already exists")

    # It will call GetUserByIdHandler(user_repo).__call__(query)
    # UserRepoImpl created earlier will be reused in this scope
    user = await mediator.query(GetUserById(message.from_user.id))
    await message.answer(f"Hello, {user=}")
    logger.info("Message sent")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    di_builder = setup_di_builder()

    async with di_builder.enter_scope("app") as di_state:
        mediator = await di_builder.execute(Mediator, "app", state=di_state)
        di_builder.bind(bind_by_type(Dependent(create_mediator_builder(mediator), scope="tg_update"), Mediator))

        dp = await di_builder.execute(aiogram.Dispatcher, "app", state=di_state)
        dp.update.outer_middleware(MediatorMiddleware(mediator, di_builder, di_state))
        dp.message.register(echo_handler)

        bot = await di_builder.execute(aiogram.Bot, "app", state=di_state)
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
