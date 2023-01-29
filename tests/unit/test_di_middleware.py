from dataclasses import dataclass
from typing import Protocol

from di import bind_by_type, Container
from di.dependent import Dependent
from di.executors import AsyncExecutor

from didiator import Command, CommandHandler, Mediator, Query, QueryDispatcherImpl, QueryHandler
from didiator.dispatchers.command import CommandDispatcherImpl
from didiator.mediator import MediatorImpl
from didiator.middlewares.di import DiMiddleware
from didiator.utils.di_builder import DiBuilderImpl


@dataclass
class User:
    user_id: int
    username: str


class Session(Protocol):
    async def commit(self) -> None:
        ...


class UserRepo(Protocol):
    async def add_user(self, user: User) -> None:
        ...

    async def update_user(self, user: User) -> None:
        ...

    async def get_user_by_id(self, user_id: int) -> User:
        ...


class UnitOfWork(Protocol):
    user: UserRepo

    async def commit(self) -> None:
        ...


@dataclass
class GetUserById(Query[User]):
    user_id: int


class GetUserByIdHandler(QueryHandler[GetUserById, User]):
    def __init__(self, uow: UnitOfWork):
        print("init get handler")

        self._uow = uow

    async def __call__(self, query: GetUserById) -> User:
        return await self._uow.user.get_user_by_id(query.user_id)


@dataclass
class CreateUser(Command[int]):
    user_id: int
    username: str


class CreateUserHandler(CommandHandler[CreateUser, int]):
    def __init__(self, uow: UnitOfWork):
        print("init create handler")
        self._uow = uow

    async def __call__(self, command: CreateUser) -> int:
        user = User(command.user_id, command.username)
        await self._uow.user.add_user(user)
        return user.user_id


@dataclass
class UpdateUser(Command[bool]):
    user_id: int
    username: str


async def handle_update_user(command: UpdateUser, uow: UnitOfWork) -> bool:
    print("Handling update user:", command, uow)
    user = User(command.user_id, command.username)
    await uow.user.update_user(user)
    return True


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

    async def add_user(self, user: User) -> None:
        self._db_mock[user.user_id] = user

    async def update_user(self, user: User) -> None:
        self._db_mock[user.user_id] = user

    async def get_user_by_id(self, user_id: int) -> User:
        if user_id not in self._db_mock:
            raise ValueError("User with given id doesn't exist")
        return self._db_mock[user_id]


class UserController:
    def __init__(self, mediator: Mediator):
        self._mediator = mediator

    async def interact_with_user(self) -> None:
        assert await self._mediator.send(CreateUser(1, "Jon")) == 1
        assert await self._mediator.query(GetUserById(1)) == User(1, "Jon")
        assert await self._mediator.send(UpdateUser(1, "Nick")) is True
        assert await self._mediator.send(UpdateUser(1, "Sam")) is True
        assert await self._mediator.query(GetUserById(1)) == User(1, "Sam")


class TestDiMiddleware:
    async def test_di_middleware_with_mediator(self) -> None:
        di_container = Container()
        di_executor = AsyncExecutor()

        di_container.bind(bind_by_type(Dependent(UnitOfWorkImpl, scope="mediator"), UnitOfWork))
        di_container.bind(bind_by_type(Dependent(UserRepoMock, scope="mediator"), UserRepo))
        di_container.bind(bind_by_type(Dependent(SessionMock, scope="mediator"), Session))

        command_dispatcher = CommandDispatcherImpl(middlewares=(
            DiMiddleware(DiBuilderImpl(di_container, di_executor, ["mediator", "mediator_request"]), cls_scope="mediator"),
        ))
        query_dispatcher = QueryDispatcherImpl(middlewares=(
            DiMiddleware(DiBuilderImpl(di_container, di_executor, ["mediator", "mediator_request"]), cls_scope="mediator"),
        ))

        command_dispatcher.register_handler(CreateUser, CreateUserHandler)
        command_dispatcher.register_handler(UpdateUser, handle_update_user)
        query_dispatcher.register_handler(GetUserById, GetUserByIdHandler)

        mediator = MediatorImpl(command_dispatcher, query_dispatcher)
        async with di_container.enter_scope("mediator") as di_state:
            scoped_mediator = mediator.bind(di_state=di_state)

            user_controller = UserController(scoped_mediator)
            await user_controller.interact_with_user()
