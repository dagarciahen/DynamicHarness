"""Budget accounting for cloud model spend."""

from __future__ import annotations


class BudgetMeter:
    """Tracks cloud token spend against an optional limit.

    ``limit=None`` means unlimited. The meter is mutated by the routing adapter
    after each cloud turn using the provider-reported token usage.
    """

    def __init__(self, limit: int | None = None) -> None:
        if limit is not None and (isinstance(limit, bool) or limit < 0):
            raise ValueError("budget limit must be a non-negative integer or null")
        self.limit = limit
        self.spent = 0

    def record(self, tokens: int) -> None:
        if tokens < 0:
            raise ValueError("recorded tokens must be non-negative")
        self.spent += tokens

    @property
    def remaining(self) -> int | None:
        return None if self.limit is None else max(0, self.limit - self.spent)

    @property
    def exhausted(self) -> bool:
        return self.limit is not None and self.spent >= self.limit
