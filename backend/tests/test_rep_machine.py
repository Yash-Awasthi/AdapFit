"""Tests for the form-check rep state machine and batch endpoint logic."""
from app.api.v1.endpoints.form_check import RepStateMachine


def test_rep_machine_counts_full_rep():
    machine = RepStateMachine(min_angle=90.0, max_angle=160.0, hysteresis=12.0)
    # Standing tall -> descending -> bottom -> ascending -> top = 1 rep
    steps = [170, 120, 85, 100, 150, 165]
    reps = 0
    completed = False
    for angle in steps:
        r = machine.process(angle)
        reps = r["count"]
        completed = r["rep_completed"] or completed
    assert reps == 1
    assert completed


def test_rep_machine_counts_multiple_reps():
    machine = RepStateMachine(min_angle=90.0, max_angle=160.0, hysteresis=12.0)
    angles = [170, 120, 85, 100, 150, 165, 120, 80, 105, 155, 168]
    reps = 0
    for angle in angles:
        reps = machine.process(angle)["count"]
    assert reps == 2


def test_rep_machine_ignores_noise():
    machine = RepStateMachine(min_angle=90.0, max_angle=160.0, hysteresis=12.0)
    # Small jitter around the bottom should not count a rep
    angles = [170, 120, 85, 88, 92, 86, 100, 150, 165, 120, 84, 87, 91, 85, 105, 155, 168]
    reps = 0
    for angle in angles:
        reps = machine.process(angle)["count"]
    assert reps == 2


def test_rep_machine_reset():
    machine = RepStateMachine()
    for angle in [170, 120, 85, 100, 150, 165]:
        machine.process(angle)
    assert machine.rep_count == 1
    machine.reset()
    assert machine.rep_count == 0
    assert machine.state == "START"


def test_rep_machine_tracks_grades():
    machine = RepStateMachine()
    machine.process(170, "A")
    machine.process(120, "B")
    machine.process(85, "C")
    machine.process(100, "B")
    machine.process(150, "A")
    machine.process(165, "A")
    assert machine.rep_count == 1
    assert machine.grades == ["C"]