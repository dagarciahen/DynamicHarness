"""Dynamic local/cloud model routing.

The router is the differentiating layer of the harness: for each model turn it
decides whether a local (Ollama) or a cloud (OpenAI-compatible, e.g. DeepSeek)
model should run, based on task type, resource load and budget.

The decision logic in :mod:`.router`, :mod:`.policy`, :mod:`.budget` and
:mod:`.health` is pure stdlib and unit-testable without the full DynamicHarness
dependency tree. :mod:`.routing_binding` is the thin integration seam that
wraps the router into a canonical ``ModelTurnBinding`` so existing runtimes
keep working unchanged.
"""

from .budget import BudgetMeter
from .health import LocalHealth, LocalHealthProbe, OllamaHealthProbe
from .policy import (
    CONFIG_FILENAME,
    BudgetPolicy,
    Pool,
    RoutingPolicy,
    TaskClass,
    load_routing_policy,
    parse_routing_policy,
)
from .router import (
    ModelRouter,
    RoutingContext,
    RoutingDecision,
    RoutingError,
    RoutingState,
    RoutingTurnAdapter,
)

__all__ = [
    "CONFIG_FILENAME",
    "BudgetMeter",
    "BudgetPolicy",
    "LocalHealth",
    "LocalHealthProbe",
    "ModelRouter",
    "OllamaHealthProbe",
    "Pool",
    "RoutingContext",
    "RoutingDecision",
    "RoutingError",
    "RoutingPolicy",
    "RoutingState",
    "RoutingTurnAdapter",
    "TaskClass",
    "load_routing_policy",
    "parse_routing_policy",
]
