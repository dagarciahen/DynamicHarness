from types import SimpleNamespace

from dynamicharness.execution.model_router.budget import BudgetMeter
from dynamicharness.execution.model_router.policy import parse_routing_policy
from dynamicharness.execution.model_router.router import (
    ModelRouter,
    RoutingContext,
    RoutingError,
    RoutingState,
    RoutingTurnAdapter,
)


def make_policy():
    return parse_routing_policy(
        {
            "routing": {
                "enabled": True,
                "default_pool": "cloud",
                "local_max_load": 0.9,
                "final_resort": "cloud",
                "pools": {
                    "local": {"local": True, "model_types": ["ollama"]},
                    "cloud": {"local": False, "model_types": ["powerful", "fast"]},
                },
                "task_classes": {
                    "simple": {"prefer": "local", "patterns": [r"\bsummar", r"\bhello"]},
                    "code": {"prefer": "cloud", "patterns": [r"\bimplement", r"\brefactor"]},
                },
                "budget": {"cloud_token_budget": 1000, "over_budget_behavior": "local"},
            }
        }
    )


def healthy_local():
    return RoutingState(local_available=True, local_load=0.0, cloud_available=True)


def test_simple_task_routes_to_local():
    router = ModelRouter(make_policy())
    decision = router.route(RoutingContext(task_text="Please summarize this report"), healthy_local())
    assert decision.pool == "local"
    assert decision.model_type == "ollama"
    assert decision.task_class == "simple"
    assert decision.confidence == 1.0


def test_code_task_routes_to_cloud():
    router = ModelRouter(make_policy())
    decision = router.route(RoutingContext(task_text="Implement a new feature"), healthy_local())
    assert decision.pool == "cloud"
    assert decision.model_type == "powerful"


def test_general_task_uses_default_pool():
    router = ModelRouter(make_policy())
    decision = router.route(RoutingContext(task_text="do something generic"), healthy_local())
    assert decision.task_class == "general"
    assert decision.pool == "cloud"


def test_unavailable_local_falls_back_to_cloud():
    router = ModelRouter(make_policy())
    state = RoutingState(local_available=False, cloud_available=True)
    decision = router.route(RoutingContext(task_text="summarize this"), state)
    assert decision.pool == "cloud"


def test_over_budget_prefers_local_even_for_cloud_tasks():
    router = ModelRouter(make_policy())
    state = RoutingState(
        local_available=True,
        local_load=0.0,
        cloud_available=True,
        cloud_budget_exhausted=True,
    )
    decision = router.route(RoutingContext(task_text="implement this"), state)
    assert decision.pool == "local"


def test_over_budget_with_local_unavailable_uses_final_resort():
    router = ModelRouter(make_policy())
    state = RoutingState(
        local_available=False,
        cloud_available=True,
        cloud_budget_exhausted=True,
    )
    decision = router.route(RoutingContext(task_text="implement this"), state)
    assert decision.pool == "cloud"
    assert decision.confidence == 0.3


def test_over_budget_error_behavior():
    policy = make_policy()
    policy = parse_routing_policy(
        {
            "routing": {
                "enabled": True,
                "default_pool": "cloud",
                "final_resort": "error",
                "pools": {
                    "local": {"local": True, "model_types": ["ollama"]},
                    "cloud": {"local": False, "model_types": ["powerful"]},
                },
                "task_classes": {},
                "budget": {"cloud_token_budget": 1000, "over_budget_behavior": "error"},
            }
        }
    )
    router = ModelRouter(policy)
    state = RoutingState(local_available=False, cloud_available=True, cloud_budget_exhausted=True)
    try:
        router.route(RoutingContext(task_text="anything"), state)
    except RoutingError:
        pass
    else:
        raise AssertionError("exhausted budget with error behavior must raise")


class _FakeCandidate:
    def __init__(self, model_type):
        self.model_type = model_type
        self.calls = []

    def turn(self, *, items, tools=(), instructions=None, options=None):
        self.calls.append((items, tools, instructions, options))

        class Usage:
            total_tokens = 50

        class Result:
            usage = Usage()

        return Result()


class _FakeRequest:
    items = [SimpleNamespace(text="summarize this"), SimpleNamespace(text="thanks")]
    tools = ()
    instructions = None
    options = {"stop": ["\n"], "tool_choice": "auto", "api_key": "secret"}


def test_adapter_routes_to_local_and_forwards_only_semantic_keys():
    router = ModelRouter(make_policy())
    local = _FakeCandidate("ollama")
    cloud = _FakeCandidate("powerful")
    budget = BudgetMeter(limit=1000)
    adapter = RoutingTurnAdapter(
        {"ollama": local, "powerful": cloud},
        router,
        budget=budget,
        state_factory=healthy_local,
    )
    adapter.adapter_id = "openai_chat"
    result = adapter.turn(_FakeRequest())
    assert result is not None
    assert len(local.calls) == 1
    assert len(cloud.calls) == 0
    forwarded = local.calls[0][3]
    assert forwarded == {"stop": ["\n"], "tool_choice": "auto"}
    assert "api_key" not in forwarded
    assert len(adapter.history) == 1
    assert adapter.history[0].pool == "local"
    assert budget.spent == 0  # local turns do not charge the cloud budget


def test_adapter_charges_cloud_budget():
    router = ModelRouter(make_policy())
    local = _FakeCandidate("ollama")
    cloud = _FakeCandidate("powerful")
    budget = BudgetMeter(limit=1000)
    adapter = RoutingTurnAdapter(
        {"ollama": local, "powerful": cloud},
        router,
        budget=budget,
        state_factory=healthy_local,
    )
    adapter.adapter_id = "openai_chat"
    request = SimpleNamespace(
        items=[SimpleNamespace(text="implement the parser")],
        tools=(),
        instructions=None,
        options={},
    )
    adapter.turn(request)
    assert len(cloud.calls) == 1
    assert budget.spent == 50
