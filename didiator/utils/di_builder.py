from collections.abc import Sequence
from typing import Any, ContextManager, Mapping, TypeVar

from di._utils.types import FusedContextManager
from di.api.executor import SupportsAsyncExecutor
from di.api.providers import DependencyProvider, DependencyProviderType
from di.api.scopes import Scope
from di.api.solved import SolvedDependent
from di.container import BindHook, Container, ContainerState
from di.dependent import Dependent

T = TypeVar("T")


class DiBuilder:
    def __init__(
        self, di_container: Container, di_executor: SupportsAsyncExecutor, di_scopes: Sequence[Scope] = (),
    ) -> None:
        self._di_container = di_container
        self._di_executor = di_executor
        self.di_scopes = di_scopes

        self._solved_dependencies: dict[Scope, dict[DependencyProviderType[Any], SolvedDependent[Any]]] = {}

    def bind(self, hook: BindHook) -> ContextManager[None]:
        return self._di_container.bind(hook)

    def enter_scope(self, scope: Scope, state: ContainerState | None = None) -> FusedContextManager[ContainerState]:
        return self._di_container.enter_scope(scope, state)

    async def execute(
        self, call: DependencyProviderType[T], scope: Scope,
        *, state: ContainerState | None = None, values: Mapping[DependencyProvider, Any] | None = None,
    ) -> T:
        solved_dependency = self.get_solved(call, scope)
        return await self._di_container.execute_async(
            solved_dependency, self._di_executor, state=state, values=values,
        )

    def get_solved(self, call: DependencyProviderType[T], scope: Scope) -> SolvedDependent[T]:
        try:
            solved_dependency = self._solved_dependencies.setdefault(scope, {})[call]
        except KeyError:
            solved_dependency = self._di_container.solve(Dependent(call, scope=scope), scopes=self.di_scopes)
            self._solved_dependencies[scope][call] = solved_dependency
        return solved_dependency
