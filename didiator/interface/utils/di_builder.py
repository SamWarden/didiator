from typing import Any, ContextManager, Mapping, TypeVar

from di._utils.types import FusedContextManager
from di.api.providers import DependencyProvider, DependencyProviderType
from di.api.scopes import Scope
from di.api.solved import SolvedDependent
from di.container import BindHook, ContainerState

T = TypeVar("T")


class DiBuilder:
    def bind(self, hook: BindHook) -> ContextManager[None]:
        raise NotImplementedError

    def enter_scope(self, scope: Scope, state: ContainerState | None = None) -> FusedContextManager[ContainerState]:
        raise NotImplementedError

    async def execute(
        self, call: DependencyProviderType[T], scope: Scope,
        *, state: ContainerState, values: Mapping[DependencyProvider, Any] | None = None,
    ) -> T:
        raise NotImplementedError

    def get_solved(self, call: DependencyProviderType[T], scope: Scope) -> SolvedDependent[T]:
        raise NotImplementedError
