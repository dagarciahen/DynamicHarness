"""Local model health probes.

A probe reports whether the local (Ollama) backend is reachable and how loaded
it is. The probe is injectable so tests and other local backends can provide
their own signal without network access.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LocalHealth:
    """A local backend health sample."""

    available: bool
    load: float = 0.0
    detail: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.load <= 1.0:
            raise ValueError("load must be within [0.0, 1.0]")


class LocalHealthProbe(Protocol):
    def probe(self) -> LocalHealth: ...


class OllamaHealthProbe:
    """Reports Ollama reachability via its local ``/api/tags`` endpoint."""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 2.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def probe(self) -> LocalHealth:
        try:
            import urllib.request

            with urllib.request.urlopen(
                f"{self.base_url}/api/tags", timeout=self.timeout
            ) as response:
                json.loads(response.read().decode("utf-8"))
            return LocalHealth(available=True, load=0.0, detail="ok")
        except Exception as exc:  # noqa: BLE001 - probe must never raise
            return LocalHealth(available=False, load=1.0, detail=str(exc))
