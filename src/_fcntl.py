"""Minimal ``fcntl`` compatibility shim.

On POSIX this re-exports the standard :mod:`fcntl` module unchanged. On Windows
``fcntl`` is unavailable, so ``flock`` becomes a no-op and the ``LOCK_*`` flags
are provided so the package can import. Cross-process advisory locking is not
implemented on Windows; this shim exists only to unblock imports and unit tests.
"""

try:
    import fcntl as _fcntl
except ImportError:  # pragma: no cover - Windows
    from types import SimpleNamespace

    LOCK_SH = 1
    LOCK_EX = 2
    LOCK_NB = 4
    LOCK_UN = 8

    def flock(fd: int, operation: int) -> None:  # noqa: ARG001
        return None

    fcntl = SimpleNamespace(
        flock=flock,
        LOCK_SH=LOCK_SH,
        LOCK_EX=LOCK_EX,
        LOCK_NB=LOCK_NB,
        LOCK_UN=LOCK_UN,
    )
else:
    fcntl = _fcntl
