from typing import AsyncGenerator, Callable, Protocol

import pytest
from di.container import bind_by_type, Container
from di.dependent import Dependent
from di.executors import AsyncExecutor


class UnitOfWork(Protocol):
    async def commit(self) -> bool:
        ...


class Repo(Protocol):
    pass


class Handler:
    def __init__(self, uow: UnitOfWork, repo: Repo):
        print("Init handler")
        self._uow = uow
        self._repo = repo

    async def handle(self, value: bool) -> bool:
        print("Start handling")
        assert value
        assert await self._uow.commit()
        print("End handling")
        return True


class Session:
    def __init__(self, uri: str):
        print("Init session")
        self.uri = uri


class RepoImpl:
    def __init__(self, session: Session):
        print("Init repo")
        self._session = session


def get_session_factory(uri: str) -> Callable[..., AsyncGenerator[Session, None]]:
    async def get_session() -> AsyncGenerator[Session, None]:
        print("Start session")
        yield Session(uri)
        print("Close session")
    return get_session


class UnitOfWorkImpl:
    def __init__(self, session: Session):
        print("Init UoW")
        self._session = session

    async def commit(self) -> bool:
        print("Commit")
        return self._session.uri == "psql://uri"


@pytest.mark.asyncio
async def test_class_initialization_with_deps() -> None:
    container = Container()
    executor = AsyncExecutor()

    container.bind(bind_by_type(Dependent(UnitOfWorkImpl, scope="request"), UnitOfWork))
    container.bind(bind_by_type(Dependent(RepoImpl, scope="request"), Repo))
    container.bind(bind_by_type(Dependent(get_session_factory("psql://uri"), scope="request"), Session))

    solved = container.solve(Dependent(Handler, scope="request"), scopes=["request"])
    print("Before scope")
    async with container.enter_scope("request") as state:
        print("Inside scope")
        handler = await container.execute_async(solved, executor=executor, state=state)
        print("After handler initialization")
        res = await handler.handle(True)

    print("Call handler")
    assert res