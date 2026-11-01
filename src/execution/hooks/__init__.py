"""DynamicHarness's single Hook Plan and per-invocation Hook Run contract."""

from __future__ import annotations

from .config import HookConfigLayer, HookPlanCompiler, ShellHookSpec
from .runtime import HookPlan, HookRun, wrap_in_system_reminder
from .types import (
    GATE_EVENTS,
    HOOK_EVENT_NAMES,
    OBSERVER_EVENTS,
    HookContext,
    HookEvent,
    HookHandler,
    HookResult,
)


def builtin_hook_handlers() -> tuple[HookHandler, ...]:
    """Return trusted framework handlers in their stable execution order."""

    return ()


__all__ = [
    "GATE_EVENTS",
    "HOOK_EVENT_NAMES",
    "OBSERVER_EVENTS",
    "HookContext",
    "HookConfigLayer",
    "HookEvent",
    "HookHandler",
    "HookPlan",
    "HookPlanCompiler",
    "HookResult",
    "HookRun",
    "ShellHookSpec",
    "builtin_hook_handlers",
    "wrap_in_system_reminder",
]
