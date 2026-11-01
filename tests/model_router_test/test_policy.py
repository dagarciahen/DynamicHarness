from pathlib import Path

from dynamicharness.execution.model_router.policy import (
    RoutingPolicy,
    load_routing_policy,
    parse_routing_policy,
)


def make_policy():
    return {
        "routing": {
            "enabled": True,
            "default_pool": "cloud",
            "pools": {
                "local": {"local": True, "model_types": ["ollama"]},
                "cloud": {"local": False, "model_types": ["powerful", "fast"]},
            },
            "task_classes": {
                "simple": {"prefer": "local", "patterns": [r"\bsummar"]},
            },
            "budget": {"cloud_token_budget": 1000, "over_budget_behavior": "local"},
        }
    }


def test_parse_policy():
    policy = parse_routing_policy(make_policy())
    assert isinstance(policy, RoutingPolicy)
    assert policy.pool_names() == ("local", "cloud")
    assert policy.pool("local").model_types == ("ollama",)
    assert policy.pool("local").local is True
    assert policy.budget.cloud_token_budget == 1000
    assert policy.local_pool_names() == ("local",)
    assert policy.cloud_pool_names() == ("cloud",)


def test_disabled_policy_returns_none():
    data = make_policy()
    data["routing"]["enabled"] = False
    assert parse_routing_policy(data) is None


def test_bare_mapping_without_wrapper():
    data = make_policy()["routing"]
    assert parse_routing_policy(data) is not None


def test_unknown_default_pool_rejected():
    data = make_policy()
    data["routing"]["default_pool"] = "nope"
    try:
        parse_routing_policy(data)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown default pool must be rejected")


def test_missing_file_returns_none():
    assert load_routing_policy(Path("__nonexistent__/model_router.yaml")) is None
