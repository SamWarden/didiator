from dataclasses import dataclass
from typing import Any, TypeVar

from di import ScopeState
from di.api.scopes import Scope

from didiator.interface.entities.request import Request
from didiator.interface.handlers import HandlerType
from didiator.interface.utils.di_builder import DiBuilder
from didiator.middlewares import Middleware

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request[Any])
DEFAULT_STATE_KEY = "di_state"


@dataclass(frozen=True)
class MediatorDiScope:
    cls_handler: Scope
    func_handler: Scope


class DiMiddleware(Middleware):
    def __init__(
        self, di_builder: DiBuilder,
        *, cls_scope: Scope = ..., func_scope: Scope = "mediator_request", state_key: str = DEFAULT_STATE_KEY,
    ) -> None:
        self._di_builder = di_builder

        mediator_scope = MediatorDiScope(func_scope if cls_scope is ... else cls_scope, func_scope)
        self._mediator_scope = mediator_scope
        self._register_di_scopes()

        self._state_key = state_key

    def _register_di_scopes(self) -> None:
        if self._mediator_scope.cls_handler not in self._di_builder.di_scopes:
            self._di_builder.di_scopes.append(self._mediator_scope.cls_handler)
        if self._mediator_scope.func_handler not in self._di_builder.di_scopes:
            self._di_builder.di_scopes.append(self._mediator_scope.func_handler)

    async def _call(
        self,
        handler: HandlerType[R, RRes],
        request: R,
        *args: Any,
        **kwargs: Any,
    ) -> RRes:
        di_state: ScopeState | None = kwargs.pop(self._state_key, None)

        if isinstance(handler, type):
            return await self._call_class_handler(handler, request, di_state, *args, **kwargs)
        return await self._call_func_handler(handler, request, di_state)

    async def _call_class_handler(
        self, handler: HandlerType[R, RRes], request: R, di_state: ScopeState | None,
        *args: Any, **kwargs: Any,
    ) -> RRes:
        async with self._di_builder.enter_scope(self._mediator_scope.func_handler, di_state) as scoped_di_state:
            handler = await self._di_builder.execute(
                handler, self._mediator_scope.cls_handler, state=scoped_di_state, values={
                    type(request): request, ScopeState: di_state,
                },
            )
            return await handler(request, *args, **kwargs)

    async def _call_func_handler(
        self, handler: HandlerType[R, RRes], request: R, di_state: ScopeState | None,
    ) -> RRes:
        async with self._di_builder.enter_scope(self._mediator_scope.func_handler, di_state) as scoped_di_state:
            return await self._di_builder.execute(
                handler, self._mediator_scope.func_handler, state=scoped_di_state, values={
                    type(request): request, ScopeState: di_state,
                },
            )
