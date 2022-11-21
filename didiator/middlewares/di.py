from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, TypeVar

from di.api.executor import SupportsAsyncExecutor
from di.api.scopes import Scope
from di.api.solved import SolvedDependent
from di.container import Container, ContainerState
from di.dependent import Dependent

from didiator.interface.entities.request import Request
from didiator.interface.handlers import HandlerType
from didiator.middlewares import Middleware

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request)
DEFAULT_STATE_KEY = "di_state"


@dataclass(frozen=True)
class MediatorDiScope:
    cls_handler: Scope
    func_handler: Scope


class DiMiddleware(Middleware):
    def __init__(
        self, di_container: Container, di_executor: SupportsAsyncExecutor, di_scopes: Sequence[Scope] = (),
        *, cls_scope: Scope = ..., func_scope: Scope = "mediator_request", state_key: str = DEFAULT_STATE_KEY,
    ) -> None:
        self._di_container = di_container
        self._di_executor = di_executor

        mediator_scope = MediatorDiScope(func_scope if cls_scope is ... else cls_scope, func_scope)
        self._di_scopes = self._get_di_scopes(tuple(di_scopes), mediator_scope)
        self._mediator_scope = mediator_scope

        self._state_key = state_key
        self._solved_handlers: dict[HandlerType[Any, Any], SolvedDependent[HandlerType[Any, Any]]] = {}

    def _get_di_scopes(self, di_scopes: tuple[Scope, ...], mediator_scope: MediatorDiScope) -> tuple[Scope, ...]:
        if mediator_scope.cls_handler not in di_scopes:
            di_scopes += (mediator_scope.cls_handler,)
        if mediator_scope.func_handler not in di_scopes:
            di_scopes += (mediator_scope.func_handler,)
        return di_scopes

    async def _call(
        self,
        handler: HandlerType[R, RRes],
        request: R,
        *args: Any,
        **kwargs: Any,
    ) -> RRes:
        di_state: ContainerState | None = kwargs.pop(self._state_key, None)

        if isinstance(handler, type):
            return await self._call_class_handler(handler, request, di_state, *args, **kwargs)
        return await self._call_func_handler(handler, request, di_state)

    async def _call_class_handler(
        self, handler: HandlerType[R, RRes], request: R, di_state: ContainerState | None,
        *args: Any, **kwargs: Any,
    ) -> RRes:
        solved_handler = self._get_cached_solved_handler(handler, self._mediator_scope.cls_handler)
        async with self._di_container.enter_scope(self._mediator_scope.func_handler, di_state) as scoped_di_state:
            handler = await self._di_container.execute_async(
                solved_handler, executor=self._di_executor, state=scoped_di_state, values={type(request): request},
            )
            return await handler(request, *args, **kwargs)

    async def _call_func_handler(
        self, handler: HandlerType[R, RRes], request: R, di_state: ContainerState | None,
    ) -> RRes:
        solved_handler = self._get_cached_solved_handler(handler, self._mediator_scope.func_handler)
        async with self._di_container.enter_scope(self._mediator_scope.func_handler, di_state) as scoped_di_state:
            return await self._di_container.execute_async(
                solved_handler, executor=self._di_executor, state=scoped_di_state, values={type(request): request},
            )

    def _get_cached_solved_handler(self, handler: HandlerType, scope: Scope) -> SolvedDependent[HandlerType]:
        try:
            solved_handler = self._solved_handlers[handler]
            print("Get cached solved handler:", solved_handler)
        except KeyError:
            solved_handler = self._di_container.solve(
                Dependent(handler, scope=scope), scopes=self._di_scopes,
            )
            self._solved_handlers[handler] = solved_handler
            print("Solve handler:", solved_handler)
        return solved_handler
