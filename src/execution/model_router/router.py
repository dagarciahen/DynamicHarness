"""Pure decision logic for dynamic local/cloud model routing."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .budget import BudgetMeter
from .policy import RoutingPolicy

_FORWARDED_TURN_KEYS = ("stop", "tool_choice")


@dataclass(frozen=True, slots=True)
class RoutingState:
    """Availability, load and budget signals visible to the router."""

    local_available: bool = True
    local_load: float = 0.0
    cloud_available: bool = True
    cloud_budget_exhausted: bool = False


@dataclass(frozen=True, slots=True)
class RoutingContext:
    """Everything the router needs to classify one model turn."""

    task_text: str = ""
    tool_names: tuple[str, ...] = ()
    instructions: str | None = None

    @classmethod
    def from_request(cls, request: Any) -> RoutingContext:
        texts: list[str] = []
        tool_names: list[str] = []
        for item in getattr(request, "items", ()) or ():
            if getattr(item, "text", None):
                texts.append(item.text)
            elif getattr(item, "output", None):
                texts.append(item.output)
            elif getattr(item, "name", None):
                texts.append(item.name)
        for tool in getattr(request, "tools", ()) or ():
            name = getattr(tool, "name", "")
            if name:
                tool_names.append(name)
        return cls(
            task_text="\n".join(texts),
            tool_names=tuple(tool_names),
            instructions=getattr(request, "instructions", None),
        )


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """The outcome of one routing decision."""

    pool: str
    model_type: str
    task_class: str
    reason: str
    confidence: float


class RoutingError(RuntimeError):
    """No model pool satisfied the policy and fallback constraints."""


class ModelRouter:
    """Classify a turn and select a local or cloud model pool."""

    def __init__(self, policy: RoutingPolicy) -> None:
        self.policy = policy

    def classify(self, context: RoutingContext) -> str | None:
        """Return the matching task class name, or ``None``."""

        haystack = f"{context.task_text}\n{context.instructions or ''}\n{' '.join(context.tool_names)}".lower()
        for task_class in self.policy.task_classes:
            for pattern in task_class.patterns:
                try:
                    if re.search(pattern, haystack):
                        return task_class.name
                except re.error:
                    continue
        return None

    def route(self, context: RoutingContext, state: RoutingState) -> RoutingDecision:
        """Pick a pool and model type for the turn."""

        task_class_name = self.classify(context) or "general"
        preferred = self._preferred_pool(task_class_name)
        ordered = [preferred] + [pool.name for pool in self.policy.pools if pool.name != preferred]

        for pool_name in ordered:
            decision = self._consider(self.policy.pool(pool_name), task_class_name, state)
            if decision is not None:
                return decision

        return self._final_resort(task_class_name, state)

    def _preferred_pool(self, task_class_name: str) -> str:
        if task_class_name != "general":
            for task_class in self.policy.task_classes:
                if task_class.name == task_class_name:
                    return task_class.prefer
        return self.policy.default_pool

    def _consider(
        self,
        pool,
        task_class_name: str,
        state: RoutingState,
    ) -> RoutingDecision | None:
        if pool is None:
            return None
        model_type = pool.model_types[0]
        if pool.local:
            if not state.local_available:
                return None
            if state.local_load > self.policy.local_max_load:
                return None
            confidence = 0.8 if state.local_load > 0.5 else 1.0
            return RoutingDecision(
                pool=pool.name,
                model_type=model_type,
                task_class=task_class_name,
                reason=f"local pool '{pool.name}' selected for '{task_class_name}'",
                confidence=confidence,
            )

        if not state.cloud_available:
            return None
        if state.cloud_budget_exhausted:
            behavior = self.policy.budget.over_budget_behavior
            if behavior == "local":
                return None
            if behavior == "error":
                return None
            return RoutingDecision(
                pool=pool.name,
                model_type=model_type,
                task_class=task_class_name,
                reason=f"cloud pool '{pool.name}' selected despite exhausted budget",
                confidence=0.6,
            )
        return RoutingDecision(
            pool=pool.name,
            model_type=model_type,
            task_class=task_class_name,
            reason=f"cloud pool '{pool.name}' selected for '{task_class_name}'",
            confidence=1.0,
        )

    def _final_resort(self, task_class_name: str, state: RoutingState) -> RoutingDecision:
        if self.policy.final_resort == "error":
            raise RoutingError(
                f"no pool satisfied the routing policy for '{task_class_name}'"
            )
        target_pools = (
            self.policy.local_pool_names()
            if self.policy.final_resort == "local"
            else self.policy.cloud_pool_names()
        )
        for pool_name in target_pools:
            pool = self.policy.pool(pool_name)
            if pool is None:
                continue
            if pool.local and (not state.local_available or state.local_load > self.policy.local_max_load):
                continue
            if not pool.local and not state.cloud_available:
                continue
            return RoutingDecision(
                pool=pool.name,
                model_type=pool.model_types[0],
                task_class=task_class_name,
                reason=f"final resort: {self.policy.final_resort} pool '{pool.name}'",
                confidence=0.3,
            )
        raise RoutingError(
            f"final resort pool '{self.policy.final_resort}' is unavailable for '{task_class_name}'"
        )


class RoutingTurnAdapter:
    """Duck-typed ``ModelTurnAdapter`` that routes every turn through a policy.

    The adapter owns a mapping of ``model_type -> candidate binding`` and calls
    the selected candidate's ``turn(...)``, forwarding only per-turn semantic
    options so each candidate keeps its own wire configuration.
    """

    def __init__(
        self,
        bindings: Mapping[str, Any],
        router: ModelRouter,
        *,
        budget: BudgetMeter | None = None,
        state_factory: Callable[[], RoutingState] | None = None,
        record_history: bool = True,
    ) -> None:
        self.bindings = dict(bindings)
        self.router = router
        self.budget = budget
        self._state_factory = state_factory or (lambda: RoutingState())
        self._record_history = record_history
        self.history: list[RoutingDecision] = []
        self.adapter_id: str = "openai_chat"

    def turn(self, request: Any) -> Any:
        context = RoutingContext.from_request(request)
        state = self._state_factory()
        decision = self.router.route(context, state)
        candidate = self.bindings.get(decision.model_type)
        if candidate is None:
            raise RoutingError(
                f"routing selected model_type '{decision.model_type}' with no candidate binding"
            )
        forwarded = _forward_options(getattr(request, "options", None))
        result = candidate.turn(
            items=getattr(request, "items", ()),
            tools=getattr(request, "tools", ()),
            instructions=getattr(request, "instructions", None),
            options=forwarded,
        )
        self._record(decision, result)
        return result

    def _record(self, decision: RoutingDecision, result: Any) -> None:
        if self._record_history:
            self.history.append(decision)
        if self.budget is not None and not self._is_local(decision.pool):
            usage = getattr(result, "usage", None)
            if usage is not None:
                self.budget.record(_total_tokens(usage))

    def _is_local(self, pool_name: str) -> bool:
        pool = self.router.policy.pool(pool_name)
        return bool(pool and pool.local)


def _forward_options(options: Any) -> dict[str, Any]:
    if not isinstance(options, Mapping):
        return {}
    return {key: options[key] for key in _FORWARDED_TURN_KEYS if key in options}


def _total_tokens(usage: Any) -> int:
    total = getattr(usage, "total_tokens", None)
    if isinstance(total, int) and total >= 0:
        return total
    input_tokens = getattr(usage, "input_tokens", 0) or 0
    output_tokens = getattr(usage, "output_tokens", 0) or 0
    return input_tokens + output_tokens
