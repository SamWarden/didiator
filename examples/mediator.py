from dataclasses import dataclass
from typing import Protocol

from di.container import bind_by_type, Container
from di.dependent import Dependent
from di.executors import AsyncExecutor

from didiator.command_dispatcher import CommandDispatcherImpl
from didiator.mediator import MediatorImpl


@dataclass
class User:
    user_id: int
    username: str


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

# ===============
# Not implemented
# ===============


class GetUserById(Query[User]):
    user_id: int


class GetUserByIdHandler(QueryHandler[GetUserById]):
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, query: GetUserById) -> User:
        return await self._uow.user.get_user_by_id(query.user_id)


class CreateUser(Command[int]):
    user_id: int
    username: str


class CreateUserHandler(CommandHandler[CreateUser]):
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def handle(self, command: CreateUser) -> int:
        user = User(command.user_id, command.username)
        self._uow.user.add_user(user)
        return user.user_id


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


async def test_mediator() -> None:
    di_container = Container()
    di_executor = AsyncExecutor()

    di_container.bind(bind_by_type(Dependent(UnitOfWorkImpl, scope="mediator"), UnitOfWork))
    di_container.bind(bind_by_type(Dependent(UserRepoMock, scope="mediator"), UserRepo))
    di_container.bind(bind_by_type(Dependent(SessionMock, scope="mediator"), Session))

    command_dispatcher = CommandDispatcherImpl(middlewares=(LoggingMiddleware(), DiMiddleware(di_container, di_executor)))
    query_dispatcher = QueryDispatcherImpl(middlewares=(LoggingMiddleware(), DiMiddleware(di_container, di_executor)))

    command_dispatcher.register_handler(CreateUser, CreateUserHandler)
    query_dispatcher.register_handler(GetUserById, GetUserByIdHandler)

    async with di_container.enter_scope("mediator") as di_state:
        mediator = MediatorImpl(command_dispatcher, query_dispatcher, middleware_data={"di_state": di_state})
        # medator = initialized_mediator.bind({"di_state": di_state})

        assert await mediator.send(CreateUser(1, "Jon")) == 1
        assert await mediator.query(GetUserById(1)) == User(1, "Jon")
