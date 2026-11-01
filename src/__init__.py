"""DynamicHarness public package surface."""

if __name__ != "dynamicharness":
    raise ImportError("Import DynamicHarness as 'dynamicharness'; install the project first.")

__version__ = "1.0.1"

_LAZY_EXPORTS = {
    "C": ("dynamicharness.config", "C"),
    "get_config": ("dynamicharness.config", "get_config"),
    "get_default_toolsets": ("dynamicharness.config", "get_default_toolsets"),
    "get_model_config": ("dynamicharness.config", "get_model_config"),
    "ApplicationRunError": ("dynamicharness.app.run", "ApplicationRunError"),
    "ApplicationRunInterrupted": ("dynamicharness.app.run", "ApplicationRunInterrupted"),
    "ApplicationRunResult": ("dynamicharness.app.run", "ApplicationRunResult"),
    "RunEventSink": ("dynamicharness.app.run", "RunEventSink"),
    "RunInfo": ("dynamicharness.app.run", "RunInfo"),
    "RunLifecycleEvent": ("dynamicharness.app.run", "RunLifecycleEvent"),
    "RunPhase": ("dynamicharness.app.run", "RunPhase"),
    "RunRejectedEvent": ("dynamicharness.app.run", "RunRejectedEvent"),
    "RunRejection": ("dynamicharness.app.run", "RunRejection"),
    "execute_app": ("dynamicharness.app.runner", "execute_app"),
    "run_app": ("dynamicharness.app.runner", "run_app"),
}


def __getattr__(name: str):
    """Preserve the public package API without loading the agent runtime eagerly."""
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    module_name, attribute = target
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals(), *_LAZY_EXPORTS})

__all__ = [
    "__version__",
    "C",
    "get_config",
    "get_default_toolsets",
    "get_model_config",
    "ApplicationRunError",
    "ApplicationRunInterrupted",
    "ApplicationRunResult",
    "RunEventSink",
    "RunInfo",
    "RunLifecycleEvent",
    "RunPhase",
    "RunRejectedEvent",
    "RunRejection",
    "execute_app",
    "run_app",
]
