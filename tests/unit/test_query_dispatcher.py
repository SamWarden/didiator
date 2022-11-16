from dataclasses import dataclass

from didiator.query import Query, QueryHandler

from didiator.query_dispatcher import QueryDispatcherImpl
from tests.mocks.middlewares import DataAdderMiddlewareMock, DataRemoverMiddlewareMock


@dataclass
class GetUserQuery(Query[int]):
    user_id: int
    username: str


@dataclass
class CollectUserDataQuery(Query[str]):
    user_id: int
    username: str


class NotQuery:
    pass


class UserId(int):
    pass


class GetUserHandler(QueryHandler[GetUserQuery, int]):
    async def __call__(self, query: GetUserQuery) -> int:
        return query.user_id


class ExtendedGetUserHandler(QueryHandler[GetUserQuery, UserId]):
    async def __call__(self, query: GetUserQuery) -> UserId:
        return UserId(query.user_id)


class CollectUserDataHandler(QueryHandler[CollectUserDataQuery, str]):
    async def __call__(self, query: CollectUserDataQuery, additional_data: str = "") -> str:
        return additional_data


async def handle_update_user(query: CollectUserDataQuery, additional_data: str = "") -> str:
    return additional_data


class TestQueryDispatcher:
    def test_init(self) -> None:
        query_dispatcher: QueryDispatcherImpl = QueryDispatcherImpl()

        assert isinstance(query_dispatcher, QueryDispatcherImpl)
        assert query_dispatcher.handlers == {}
        assert query_dispatcher.middlewares == ()

    async def test_query_handler_registration(self, query_dispatcher: QueryDispatcherImpl) -> None:
        query_dispatcher.register_handler(GetUserQuery, GetUserHandler)
        assert query_dispatcher.handlers == {GetUserQuery: GetUserHandler}

        query_dispatcher.register_handler(CollectUserDataQuery, CollectUserDataHandler)
        assert query_dispatcher.handlers == {GetUserQuery: GetUserHandler, CollectUserDataQuery: CollectUserDataHandler}

        query_dispatcher.register_handler(GetUserQuery, ExtendedGetUserHandler)
        assert query_dispatcher.handlers == {GetUserQuery: ExtendedGetUserHandler, CollectUserDataQuery: CollectUserDataHandler}

    async def test_initialization_with_middlewares(self) -> None:
        middleware1 = DataAdderMiddlewareMock()
        query_dispatcher = QueryDispatcherImpl(middlewares=(middleware1,))
        assert query_dispatcher.middlewares == (middleware1,)

        middleware2 = DataRemoverMiddlewareMock()
        query_dispatcher = QueryDispatcherImpl(middlewares=[middleware1, middleware2])
        assert query_dispatcher.middlewares == (middleware1, middleware2)

    async def test_query_querying(self, query_dispatcher: QueryDispatcherImpl) -> None:
        query_dispatcher.register_handler(GetUserQuery, GetUserHandler)

        res = await query_dispatcher.query(GetUserQuery(1, "Jon"))
        assert res == 1

    async def test_query_querying_with_middlewares(self) -> None:
        middleware1 = DataAdderMiddlewareMock(middleware_data="data", additional_data="value")
        middleware2 = DataRemoverMiddlewareMock("middleware_data")
        query_dispatcher = QueryDispatcherImpl(middlewares=[middleware1, middleware2])

        query_dispatcher.register_handler(CollectUserDataQuery, CollectUserDataHandler)

        res = await query_dispatcher.query(CollectUserDataQuery(1, "Sam"))
        assert res == "value"

    async def test_query_querying_with_function_handler(self) -> None:
        query_dispatcher = QueryDispatcherImpl()
        query_dispatcher.register_handler(CollectUserDataQuery, handle_update_user)

        res = await query_dispatcher.query(CollectUserDataQuery(1, "Sam"), additional_data="value")
        assert res == "value"

    async def test_query_querying_with_middlewares_and_function_handler(self) -> None:
        middleware1 = DataAdderMiddlewareMock(middleware_data="data", additional_data="value")
        middleware2 = DataRemoverMiddlewareMock("middleware_data")
        query_dispatcher = QueryDispatcherImpl(middlewares=[middleware1, middleware2])

        query_dispatcher.register_handler(CollectUserDataQuery, handle_update_user)

        res = await query_dispatcher.query(CollectUserDataQuery(1, "Sam"))
        assert res == "value"
