from dynamicharness.execution.model_router.budget import BudgetMeter


def test_unlimited_meter_never_exhausts():
    meter = BudgetMeter()
    assert meter.remaining is None
    assert not meter.exhausted
    meter.record(1234)
    assert meter.spent == 1234
    assert not meter.exhausted


def test_limited_meter_tracks_remaining():
    meter = BudgetMeter(limit=100)
    assert meter.remaining == 100
    meter.record(40)
    assert meter.remaining == 60
    assert not meter.exhausted
    meter.record(60)
    assert meter.remaining == 0
    assert meter.exhausted


def test_negative_limit_rejected():
    try:
        BudgetMeter(limit=-1)
    except ValueError:
        pass
    else:
        raise AssertionError("negative limit must be rejected")


def test_negative_record_rejected():
    meter = BudgetMeter(limit=10)
    try:
        meter.record(-5)
    except ValueError:
        pass
    else:
        raise AssertionError("negative record must be rejected")
