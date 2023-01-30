from collections.abc import Mapping
from typing import Any, ContextManager, TypeVar

from di import Container, ScopeState, SolvedDependent
from di._container import BindHook
from di._utils.types import FusedContextManager
from di.api.executor import SupportsAsyncExecutor
from di.api.providers import DependencyProvider, DependencyProviderType
from di.api.scopes import Scope
from di.dependent import Dependent

from didiator.interface.utils.di_builder import DiBuilder

DependencyType = TypeVar("DependencyType")


class DiBuilderImpl(DiBuilder):
    def __init__(
        self, di_container: Container, di_executor: SupportsAsyncExecutor, di_scopes: list[Scope] | None = None,
        *, solved_dependencies: dict[Scope, dict[DependencyProviderType[Any], SolvedDependent[Any]]] | None = None,
    ) -> None:
        self._di_container = di_container
        self._di_executor = di_executor
        if di_scopes is None:
            di_scopes = []
        self.di_scopes = di_scopes

        if solved_dependencies is None:
            solved_dependencies = {}
        self._solved_dependencies = solved_dependencies

    def bind(self, hook: BindHook) -> ContextManager[None]:
        return self._di_container.bind(hook)

    def enter_scope(self, scope: Scope, state: ScopeState | None = None) -> FusedContextManager[ScopeState]:
        return self._di_container.enter_scope(scope, state)

    async def execute(
        self, call: DependencyProviderType[DependencyType], scope: Scope,
        *, state: ScopeState, values: Mapping[DependencyProvider, Any] | None = None,
    ) -> DependencyType:
        solved_dependency = self.solve(call, scope)
        return await solved_dependency.execute_async(executor=self._di_executor, state=state, values=values)

    def solve(self, call: DependencyProviderType[DependencyType], scope: Scope) -> SolvedDependent[DependencyType]:
        solved_scope_dependencies = self._solved_dependencies.setdefault(scope, {})
        try:
            solved_dependency = solved_scope_dependencies[call]
        except KeyError:
            solved_dependency = self._di_container.solve(Dependent(call, scope=scope), scopes=self.di_scopes)
            solved_scope_dependencies[call] = solved_dependency
        return solved_dependency

    def copy(self) -> "DiBuilderImpl":
        di_container = Container()
        di_container._bind_hooks = self._di_container._bind_hooks.copy()  # noqa
        return DiBuilderImpl(
            di_container, self._di_executor, self.di_scopes, solved_dependencies=self._solved_dependencies,
        )
