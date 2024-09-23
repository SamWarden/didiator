import asyncio
import logging
from dataclasses import dataclass
from typing import Protocol

from dishka import AsyncContainer, make_async_container, provide, Provider, Scope

from didiator import Handler, Mediator, Request
from didiator.ioc.dishka import DishkaIoc
from didiator.mediator import MediatorImpl

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
class CreateUser(Request[int]):
    user_id: int
    username: str


class CreateUserHandler(Handler[CreateUser, int]):
    def __init__(self, user_repo: UserRepo) -> None:
        self._user_repo = user_repo

    async def __call__(self, command: CreateUser) -> int:
        user = User(id=command.user_id, username=command.username)
        await self._user_repo.add_user(user)
        await self._user_repo.commit()
        return user.id


# Get user query and its handler
# @dataclass(frozen=True)
# class GetUserById(Query[User]):
#     user_id: int
#
#
# async def handle_get_user_by_id(query: GetUserById, user_repo: UserRepo) -> User:
#     user = await user_repo.get_user_by_id(query.user_id)
#     return user


class UserRepoImpl(UserRepo):
    def __init__(self) -> None:
        self._db_mock: dict[int, User] = {}

    async def add_user(self, user: User) -> None:
        self._db_mock[user.id] = user

    async def get_user_by_id(self, user_id: int) -> User:
        if user_id not in self._db_mock:
            raise ValueError("User with given id doesn't exist")
        return self._db_mock[user_id]

    async def commit(self) -> None:
        ...


def build_mediator(container: AsyncContainer) -> Mediator:
    mediator = MediatorImpl(ioc=DishkaIoc(container), middlewares=[])

    mediator.register_request_handler(CreateUser, CreateUserHandler)
    # mediator.register_request_handler(GetUserById, handle_get_user_by_id)

    return mediator


class MainProvider(Provider):
    # get_user_by_id = provide(GetUserByIdHandler, scope=Scope.REQUEST)
    create_user_handler = provide(CreateUserHandler, scope=Scope.REQUEST)

    @provide(scope=Scope.REQUEST)
    def user_repo(self) -> UserRepo:
        return UserRepoImpl()


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    # di_builder = setup_di_builder()
    container = make_async_container(MainProvider())
    mediator = build_mediator(container)

    # It will call CreateUserHandler(UserRepoImpl()).__call__(command)
    # UserRepoImpl() created and injected automatically
    user_id = await mediator.send(CreateUser(1, "Jon"))
    logger.info(f"Created a user with id: {user_id}")

    # It will call handle_get_user_by_id(query, user_repo)
    # UserRepoImpl created earlier will be reused in this scope
    # user = await mediator.send(GetUserById(user_id))
    # logger.info(f"User: {user}")


if __name__ == "__main__":
    asyncio.run(main())
