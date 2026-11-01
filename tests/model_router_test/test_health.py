from dynamicharness.execution.model_router.health import LocalHealth, OllamaHealthProbe


def test_local_health_load_bounds():
    health = LocalHealth(available=True, load=0.5)
    assert health.available is True
    try:
        LocalHealth(available=True, load=1.5)
    except ValueError:
        pass
    else:
        raise AssertionError("load out of range must be rejected")


def test_unreachable_backend_reports_unavailable():
    probe = OllamaHealthProbe(base_url="http://127.0.0.1:1", timeout=0.2)
    health = probe.probe()
    assert health.available is False
