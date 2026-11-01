"""Integration tests for the routing ``ModelTurnBinding`` seam.

These tests exercise the layer that wraps candidate bindings into one routed
binding, without needing a live Ollama or cloud endpoint.
"""

from __future__ import annotations

from types import SimpleNamespace

from dynamicharness.execution.model_binding import ModelTurnBinding
from dynamicharness.execution.model_protocol import ModelTurnResult
from dynamicharness.execution.model_router.health import LocalHealth
from dynamicharness.execution.model_router.policy import parse_routing_policy
from dynamicharness.execution.model_router.router import ModelRouter
from dynamicharness.execution.model_router.routing_binding import (
    ROUTING_MODEL_TYPE,
    build_routing_binding,
)


class _FakeAdapter:
    def __init__(self, adapter_id: str, model_id: str):
        self.adapter_id = adapter_id
        self.model_id = model_id
        self.calls: list = []

    def turn(self, request):
        self.calls.append(request)
        return ModelTurnResult(items=())


class _HealthyLocal:
    def probe(self) -> LocalHealth:
        return LocalHealth(available=True, load=0.0)


def _binding(model_type: str, model_id: str, adapter_id: str = "openai_chat") -> ModelTurnBinding:
    return ModelTurnBinding(
        model_type=model_type,
        model_id=model_id,
        adapter=_FakeAdapter(adapter_id, model_id),
    )


def _policy():
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
                    "simple": {"prefer": "local", "patterns": [r"\bsummar"]},
                    "research": {"prefer": "cloud", "patterns": [r"\barxiv", r"\bpaper"]},
                    "code": {"prefer": "cloud", "patterns": [r"\bimplement"]},
                },
                "budget": {"cloud_token_budget": 1000, "over_budget_behavior": "local"},
            }
        }
    )


def _request(text: str):
    return SimpleNamespace(
        items=[SimpleNamespace(text=text)],
        tools=(),
        instructions=None,
        options={},
    )


def test_binding_wraps_candidates_under_routing_type():
    local = _binding("ollama", "ollama/qwen")
    cloud = _binding("powerful", "openai/gpt")
    binding = build_routing_binding(
        {"ollama": local, "powerful": cloud},
        ModelRouter(_policy()),
        health=_HealthyLocal(),
    )
    assert binding.model_type == ROUTING_MODEL_TYPE
    assert binding.adapter_id == "openai_chat"


def test_binding_rejects_mixed_adapter_kinds():
    local = _binding("ollama", "ollama/qwen", adapter_id="openai_chat")
    cloud = _binding("powerful", "anthropic/claude", adapter_id="anthropic_messages")
    try:
        build_routing_binding({"ollama": local, "powerful": cloud}, ModelRouter(_policy()))
    except ValueError as exc:
        assert "single wire adapter kind" in str(exc)
    else:
        raise AssertionError("mixed adapter kinds must be rejected")


def test_binding_rejects_empty_candidates():
    try:
        build_routing_binding({}, ModelRouter(_policy()))
    except ValueError as exc:
        assert "at least one candidate" in str(exc)
    else:
        raise AssertionError("empty candidate set must be rejected")


def test_simple_turn_routes_local_and_heavy_turn_routes_cloud():
    local = _binding("ollama", "ollama/qwen")
    cloud = _binding("powerful", "openai/gpt")
    binding = build_routing_binding(
        {"ollama": local, "powerful": cloud},
        ModelRouter(_policy()),
        health=_HealthyLocal(),
    )
    adapter = binding.adapter

    adapter.turn(_request("Please summarize this section"))
    adapter.turn(_request("Implement the architecture from this arxiv paper"))

    assert len(local.adapter.calls) == 1
    assert len(cloud.adapter.calls) == 1
    assert [decision.pool for decision in adapter.history] == ["local", "cloud"]


def test_local_unavailable_falls_back_to_cloud():
    local = _binding("ollama", "ollama/qwen")
    cloud = _binding("powerful", "openai/gpt")

    class _UnavailableLocal:
        def probe(self) -> LocalHealth:
            return LocalHealth(available=False, load=1.0)

    binding = build_routing_binding(
        {"ollama": local, "powerful": cloud},
        ModelRouter(_policy()),
        health=_UnavailableLocal(),
    )
    binding.adapter.turn(_request("summarize this"))
    assert len(local.adapter.calls) == 0
    assert len(cloud.adapter.calls) == 1
