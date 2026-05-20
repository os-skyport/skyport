from collections import deque

from skyport.core.engine import SimulationEngine
from skyport.core.models import Counter, CounterKind, Passenger, PassengerClass, default_counters
from skyport.io.parser import load_passengers
from skyport.schedulers import FCFSScheduler, HybridMLQScheduler


def test_assignment_input_runs_to_completion():
    passengers = load_passengers("input.txt")
    engine = SimulationEngine(passengers, default_counters(), HybridMLQScheduler())

    snapshot = engine.run()

    assert snapshot.metrics.completed_count == 50
    assert snapshot.metrics.overall_att == 15.88


def test_same_tick_completion_then_dispatch():
    passengers = [
        Passenger("P01", 0, PassengerClass.FIRST, 1),
        Passenger("P02", 1, PassengerClass.FIRST, 1),
    ]
    engine = SimulationEngine(passengers, default_counters(), FCFSScheduler())

    engine.tick()
    snapshot = engine.tick()

    messages = [event.message for event in snapshot.events_this_tick]
    assert any("COMPLETE P01" in message for message in messages)
    assert any("DISPATCH P02" in message for message in messages)


def test_non_preemptive_completion_invariant():
    passengers = load_passengers("input.txt")
    engine = SimulationEngine(passengers, default_counters(), HybridMLQScheduler())

    engine.run()

    for passenger in engine.completed:
        assert passenger.completion_time - passenger.service_start_time == passenger.service_time


def test_hybrid_dedicated_counter_uses_sjf_inside_own_queue():
    queues = {
        PassengerClass.FIRST: deque(
            [
                Passenger("P01", 0, PassengerClass.FIRST, 12),
                Passenger("P02", 0, PassengerClass.FIRST, 5),
            ]
        ),
        PassengerClass.BUSINESS: deque(),
        PassengerClass.ECONOMY: deque(),
    }

    selected = HybridMLQScheduler().select(0, Counter("C1", CounterKind.FIRST_ONLY), queues)

    assert selected.passenger_id == "P02"


def test_hybrid_flex_counter_uses_priority_as_sjf_tie_breaker():
    queues = {
        PassengerClass.FIRST: deque([Passenger("P01", 0, PassengerClass.FIRST, 6)]),
        PassengerClass.BUSINESS: deque([Passenger("P02", 0, PassengerClass.BUSINESS, 6)]),
        PassengerClass.ECONOMY: deque([Passenger("P03", 0, PassengerClass.ECONOMY, 6)]),
    }

    selected = HybridMLQScheduler().select(0, Counter("C4", CounterKind.FLEX), queues)

    assert selected.passenger_id == "P01"


def test_hybrid_dedicated_counter_work_steals_when_own_queue_empty():
    queues = {
        PassengerClass.FIRST: deque([Passenger("P01", 0, PassengerClass.FIRST, 7)]),
        PassengerClass.BUSINESS: deque(),
        PassengerClass.ECONOMY: deque([Passenger("P02", 0, PassengerClass.ECONOMY, 3)]),
    }

    selected = HybridMLQScheduler().select(0, Counter("C2", CounterKind.BUSINESS_ONLY), queues)

    assert selected.passenger_id == "P02"


def test_hybrid_economy_queue_promotes_aged_passengers_with_hrrn():
    queues = {
        PassengerClass.FIRST: deque(),
        PassengerClass.BUSINESS: deque(),
        PassengerClass.ECONOMY: deque(
            [
                Passenger("P01", 0, PassengerClass.ECONOMY, 9),
                Passenger("P02", 8, PassengerClass.ECONOMY, 3),
            ]
        ),
    }

    selected = HybridMLQScheduler().select(12, Counter("C3", CounterKind.ECONOMY_ONLY), queues)

    assert selected.passenger_id == "P01"

