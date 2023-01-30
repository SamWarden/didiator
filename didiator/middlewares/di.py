from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypeVar

from di import ScopeState
from di.api.providers import DependencyProvider
from di.api.scopes import Scope

from didiator.interface.entities.request import Request
from didiator.interface.handlers import HandlerType
from didiator.interface.utils.di_builder import DiBuilder
from didiator.middlewares import Middleware

RRes = TypeVar("RRes")
R = TypeVar("R", bound=Request[Any])


@dataclass(frozen=True)
class DiScopes:
    cls_handler: Scope = ...
    func_handler: Scope = "mediator_request"

    def __post_init__(self) -> None:
        if self.cls_handler is ...:
            object.__setattr__(self, "cls_handler", self.func_handler)


@dataclass(frozen=True)
class DiKeys:
    state: str = "di_state"
    values: str = "di_values"
    builder: str = "di_builder"


class DiMiddleware(Middleware):
    def __init__(
        self, di_builder: DiBuilder,
        *, scopes: DiScopes | None = None, di_keys: DiKeys | None = None,
    ) -> None:
        self._di_builder = di_builder

        if scopes is None:
            scopes = DiScopes()
        self._di_scopes = scopes
        self._register_di_scopes()

        if di_keys is None:
            di_keys = DiKeys()
        self._di_keys = di_keys

    def _register_di_scopes(self) -> None:
        if self._di_scopes.cls_handler not in self._di_builder.di_scopes:
            self._di_builder.di_scopes.append(self._di_scopes.cls_handler)
        if self._di_scopes.func_handler not in self._di_builder.di_scopes:
            self._di_builder.di_scopes.append(self._di_scopes.func_handler)

    async def _call(
        self,
        handler: HandlerType[R, RRes],
        request: R,
        *args: Any,
        **kwargs: Any,
    ) -> RRes:
        di_state: ScopeState | None = kwargs.pop(self._di_keys.state, None)
        di_values: Mapping[DependencyProvider, Any] = kwargs.pop(self._di_keys.values, {})
        di_builder: DiBuilder = kwargs.pop(self._di_keys.builder, self._di_builder)

        if isinstance(handler, type):
            return await self._call_class_handler(handler, request, di_builder, di_state, di_values, *args, **kwargs)
        return await self._call_func_handler(handler, request, di_builder, di_state, di_values)

    async def _call_class_handler(
        self, handler: HandlerType[R, RRes], request: R, di_builder: DiBuilder,
        di_state: ScopeState | None, di_values: Mapping[DependencyProvider, Any],
        *args: Any, **kwargs: Any,
    ) -> RRes:
        async with di_builder.enter_scope(self._di_scopes.func_handler, di_state) as scoped_di_state:
            handler = await di_builder.execute(
                handler, self._di_scopes.cls_handler, state=scoped_di_state, values={
                    type(request): request,
                } | di_values,
            )
            return await handler(request, *args, **kwargs)

    async def _call_func_handler(
        self, handler: HandlerType[R, RRes], request: R, di_builder: DiBuilder,
        di_state: ScopeState | None, di_values: Mapping[DependencyProvider, Any],
    ) -> RRes:
        async with di_builder.enter_scope(self._di_scopes.func_handler, di_state) as scoped_di_state:
            return await di_builder.execute(
                handler, self._di_scopes.func_handler, state=scoped_di_state, values={
                    type(request): request,
                } | di_values,
            )
