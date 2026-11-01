"""Routing policy configuration for the dynamic model router.

The policy is a plain mapping (loaded from YAML by the harness) plus stdlib
dataclasses, so the decision logic stays dependency-free and unit-testable
outside the full DynamicHarness environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

CONFIG_FILENAME = "model_router.yaml"

_OVER_BUDGET_BEHAVIORS = {"local", "cloud_overage", "error"}
_FINAL_RESORT_BEHAVIORS = {"cloud", "local", "error"}


@dataclass(frozen=True, slots=True)
class Pool:
    """A named set of model types that share a locality (local or cloud)."""

    name: str
    model_types: tuple[str, ...]
    local: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("pool name must be non-empty")
        if not self.model_types:
            raise ValueError(f"pool '{self.name}' must declare at least one model_type")
        object.__setattr__(self, "model_types", tuple(self.model_types))


@dataclass(frozen=True, slots=True)
class TaskClass:
    """A task bucket that maps matched turns to a preferred pool."""

    name: str
    prefer: str
    patterns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("task class name must be non-empty")
        if not self.prefer:
            raise ValueError(f"task class '{self.name}' must declare a preferred pool")
        object.__setattr__(self, "patterns", tuple(self.patterns))


@dataclass(frozen=True, slots=True)
class BudgetPolicy:
    """Cloud spend budget and what to do when it is exhausted."""

    cloud_token_budget: int | None = None
    over_budget_behavior: str = "local"

    def __post_init__(self) -> None:
        if self.over_budget_behavior not in _OVER_BUDGET_BEHAVIORS:
            raise ValueError(
                f"over_budget_behavior must be one of {sorted(_OVER_BUDGET_BEHAVIORS)}"
            )
        if self.cloud_token_budget is not None and (
            isinstance(self.cloud_token_budget, bool) or self.cloud_token_budget < 0
        ):
            raise ValueError("cloud_token_budget must be a non-negative integer or null")


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    """The full routing configuration."""

    default_pool: str = "cloud"
    local_max_load: float = 0.9
    final_resort: str = "cloud"
    pools: tuple[Pool, ...] = ()
    task_classes: tuple[TaskClass, ...] = ()
    budget: BudgetPolicy = field(default_factory=BudgetPolicy)

    def __post_init__(self) -> None:
        if not self.pools:
            raise ValueError("routing policy requires at least one pool")
        names = [pool.name for pool in self.pools]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate pool names: {names}")
        if self.default_pool not in names:
            raise ValueError(
                f"default_pool '{self.default_pool}' is not a declared pool; got {names}"
            )
        if not 0.0 <= self.local_max_load <= 1.0:
            raise ValueError("local_max_load must be within [0.0, 1.0]")
        if self.final_resort not in _FINAL_RESORT_BEHAVIORS:
            raise ValueError(f"final_resort must be one of {sorted(_FINAL_RESORT_BEHAVIORS)}")
        for task_class in self.task_classes:
            if task_class.prefer not in names:
                raise ValueError(
                    f"task class '{task_class.name}' prefers unknown pool "
                    f"'{task_class.prefer}'; got {names}"
                )
        object.__setattr__(self, "pools", tuple(self.pools))
        object.__setattr__(self, "task_classes", tuple(self.task_classes))

    def pool(self, name: str) -> Pool | None:
        for pool in self.pools:
            if pool.name == name:
                return pool
        return None

    def pool_names(self) -> tuple[str, ...]:
        return tuple(pool.name for pool in self.pools)

    def local_pool_names(self) -> tuple[str, ...]:
        return tuple(pool.name for pool in self.pools if pool.local)

    def cloud_pool_names(self) -> tuple[str, ...]:
        return tuple(pool.name for pool in self.pools if not pool.local)


def parse_routing_policy(raw: Mapping[str, Any]) -> RoutingPolicy | None:
    """Parse a routing policy mapping, or ``None`` when routing is disabled.

    Accepts either the ``routing:`` wrapper block or a bare policy mapping.
    """

    if not isinstance(raw, dict):
        return None
    data = raw.get("routing", raw)
    if not isinstance(data, dict):
        return None
    if data.get("enabled") is False:
        return None

    pools_raw = data.get("pools", {})
    if not isinstance(pools_raw, dict):
        raise ValueError("routing.pools must be a mapping of pool name to pool config")

    pools = tuple(_parse_pool(name, value) for name, value in pools_raw.items())

    task_classes = tuple(
        _parse_task_class(name, value)
        for name, value in (data.get("task_classes") or {}).items()
    )

    budget_raw = data.get("budget") or {}
    if not isinstance(budget_raw, dict):
        raise ValueError("routing.budget must be a mapping")
    budget = BudgetPolicy(
        cloud_token_budget=_optional_int(budget_raw.get("cloud_token_budget")),
        over_budget_behavior=str(budget_raw.get("over_budget_behavior", "local")),
    )

    return RoutingPolicy(
        default_pool=str(data.get("default_pool", "cloud")),
        local_max_load=float(data.get("local_max_load", 0.9)),
        final_resort=str(data.get("final_resort", "cloud")),
        pools=pools,
        task_classes=task_classes,
        budget=budget,
    )


def load_routing_policy(path: Path | str) -> RoutingPolicy | None:
    """Load the routing policy from ``config/model_router.yaml``.

    Returns ``None`` when the file is absent or routing is disabled, so the
    caller can transparently fall back to single-model resolution.
    """

    path = Path(path).expanduser()
    if not path.exists():
        return None
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - harness always provides pyyaml
        raise RuntimeError("pyyaml is required to load the routing policy") from exc

    with path.open("r", encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}
    return parse_routing_policy(raw)


def _parse_pool(name: Any, value: Any) -> Pool:
    if not isinstance(value, dict):
        raise ValueError(f"pool '{name}' must be a mapping")
    model_types = value.get("model_types")
    if isinstance(model_types, str):
        model_types = [model_types]
    if not isinstance(model_types, (list, tuple)) or not model_types:
        raise ValueError(f"pool '{name}' requires a non-empty model_types list")
    return Pool(
        name=str(name),
        model_types=tuple(str(mt) for mt in model_types),
        local=bool(value.get("local", False)),
    )


def _parse_task_class(name: Any, value: Any) -> TaskClass:
    if isinstance(value, str):
        value = {"prefer": value}
    if not isinstance(value, dict):
        raise ValueError(f"task class '{name}' must be a mapping")
    patterns = value.get("patterns", ())
    if isinstance(patterns, str):
        patterns = [patterns]
    if patterns is None:
        patterns = ()
    return TaskClass(
        name=str(name),
        prefer=str(value.get("prefer", "")),
        patterns=tuple(str(pattern) for pattern in patterns),
    )


def _optional_int(value: Any) -> int | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise ValueError("budget values must be integers")
    return int(value)
