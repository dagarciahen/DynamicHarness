"""Integration seam: wrap the router into a canonical ``ModelTurnBinding``.

This module imports the DynamicHarness model protocol so existing runtimes accept the
routed binding unchanged. Import it lazily from the agent factory so the pure
router remains importable without the full dependency tree.
"""

from __future__ import annotations

from collections.abc import Mapping

from dynamicharness.config.llm_config import LLMConfig
from dynamicharness.execution.model_binding import ModelTurnBinding

from .budget import BudgetMeter
from .health import LocalHealthProbe, OllamaHealthProbe
from .policy import RoutingPolicy
from .router import ModelRouter, RoutingState, RoutingTurnAdapter

ROUTING_MODEL_TYPE = "routing"
ROUTING_MODEL_ID = "routing"


def build_routing_binding(
    bindings: Mapping[str, ModelTurnBinding],
    router: ModelRouter,
    *,
    budget: BudgetMeter | None = None,
    health: LocalHealthProbe | None = None,
) -> ModelTurnBinding:
    """Wrap a set of candidate bindings behind one routed ``ModelTurnBinding``."""

    if not bindings:
        raise ValueError("routing requires at least one candidate binding")

    adapter_kinds = {binding.adapter_id for binding in bindings.values()}
    if len(adapter_kinds) != 1:
        raise ValueError(
            "routing pools must share a single wire adapter kind; "
            f"got {sorted(adapter_kinds)}"
        )

    has_local = bool(router.policy.local_pool_names())
    adapter = RoutingTurnAdapter(
        bindings,
        router,
        budget=budget,
        state_factory=_state_factory(budget, health, has_local),
    )
    adapter.adapter_id = adapter_kinds.pop()
    return ModelTurnBinding(
        model_type=ROUTING_MODEL_TYPE,
        model_id=ROUTING_MODEL_ID,
        adapter=adapter,
        options={},
        max_tokens=0,
        context_window=0,
        max_output_tokens=None,
        input_token_reserve=0,
        input_token_limit=0,
        requests_per_minute=0,
        description="Dynamic local/cloud model router",
    )


def build_routing_binding_from_config(
    llm_config: LLMConfig,
    policy: RoutingPolicy,
    *,
    model_cache: bool = True,
    budget: BudgetMeter | None = None,
    health: LocalHealthProbe | None = None,
) -> ModelTurnBinding:
    """Resolve every pooled model type and wrap them in a routed binding."""

    from dynamicharness.integrations.litellm.model_binding import (
        resolve_litellm_model_turn_binding,
    )

    budget = budget if budget is not None else _budget_from_policy(policy)
    health = health if health is not None else OllamaHealthProbe()
    bindings: dict[str, ModelTurnBinding] = {}
    for pool in policy.pools:
        for model_type in pool.model_types:
            bindings[model_type] = resolve_litellm_model_turn_binding(
                model_type,
                llm_config=llm_config,
                model_cache=model_cache,
            )
    return build_routing_binding(bindings, ModelRouter(policy), budget=budget, health=health)


def _budget_from_policy(policy: RoutingPolicy) -> BudgetMeter:
    return BudgetMeter(limit=policy.budget.cloud_token_budget)


def _state_factory(
    budget: BudgetMeter | None,
    health: LocalHealthProbe | None,
    has_local: bool,
):
    def factory() -> RoutingState:
        local = health.probe() if (has_local and health is not None) else None
        return RoutingState(
            local_available=local.available if local is not None else False,
            local_load=local.load if local is not None else 1.0,
            cloud_available=True,
            cloud_budget_exhausted=budget.exhausted if budget is not None else False,
        )

    return factory
