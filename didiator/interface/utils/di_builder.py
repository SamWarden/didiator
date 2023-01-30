from collections.abc import Mapping
from typing import Any, ContextManager, Protocol, TypeVar

from di import ScopeState, SolvedDependent
from di._container import BindHook
from di._utils.types import FusedContextManager
from di.api.providers import DependencyProvider, DependencyProviderType
from di.api.scopes import Scope

DependencyType = TypeVar("DependencyType")


class DiBuilder(Protocol):
    di_scopes: list[Scope]

    def bind(self, hook: BindHook) -> ContextManager[None]:
        raise NotImplementedError

    def enter_scope(self, scope: Scope, state: ScopeState | None = None) -> FusedContextManager[ScopeState]:
        raise NotImplementedError

    async def execute(
        self, call: DependencyProviderType[DependencyType], scope: Scope,
        *, state: ScopeState, values: Mapping[DependencyProvider, Any] | None = None,
    ) -> DependencyType:
        raise NotImplementedError

    def solve(self, call: DependencyProviderType[DependencyType], scope: Scope) -> SolvedDependent[DependencyType]:
        raise NotImplementedError

    def copy(self) -> "DiBuilder":
        raise NotImplementedError
