"""Application composition root for built-in Agent runtimes."""

from __future__ import annotations

from dynamicharness.execution.agent_runtime import (
    AgentRuntime,
    RuntimeDefinition,
    RuntimeFactory,
    RuntimeRegistry,
)


def build_builtin_runtime_registry(
    *,
    smolagents_factory: RuntimeFactory | None = None,
) -> RuntimeRegistry:
    """Build the production registry for DynamicHarness's built-in runtimes."""

    smolagents_readiness = None
    if smolagents_factory is None:

        def build_smolagents(definition: RuntimeDefinition) -> AgentRuntime:
            from dynamicharness.runtimes.smolagents.runtime_factory import SmolagentsRuntimeFactory

            return SmolagentsRuntimeFactory()(definition)

        smolagents_factory = build_smolagents

        def smolagents_readiness() -> None:
            from importlib import import_module

            try:
                import_module("smolagents")
            except ImportError as error:
                raise RuntimeError(
                    "The smol runtime is not installed. Install 'DynamicHarness[smol]' "
                    "or run uv sync --locked --extra smol in the checkout."
                ) from error

    registry = RuntimeRegistry()
    from dynamicharness.runtimes.smolagents.metadata import (
        CAPABILITIES as SMOLAGENTS_CAPABILITIES,
    )

    registry.register(
        "smolagents",
        capabilities=SMOLAGENTS_CAPABILITIES,
        factory=smolagents_factory,
        readiness=smolagents_readiness,
    )

    return registry
