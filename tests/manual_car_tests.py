import pytest

from car_simulator import *

m = ManualCar()

def test_start_engine():
    m.start_car()
    assert m._engine.rpm == m._engine._rpm_idle
    assert m._engine._running

def test_raises_clutch_engaged_error():
    with pytest.raises(Transmission.ClutchEngagedError):
        m.shift("1")

def test_raises_engine_redline_error():
    with pytest.raises(Engine.EngineRedlineError):
        [m.accelerate() for _ in range(200)]

def test_raises_engine_destroyed_error():
    with pytest.raises(Engine.EngineDestroyedError):
        for _ in range(10):
            try:
                m.accelerate()
            except Engine.EngineRedlineError:
                pass

def test_engine_destroyed():
    assert m._engine._destroyed

def test_starting_destroyed_engine_raises():
    with pytest.raises(Engine.EngineDestroyedError):
        m.start_car()
