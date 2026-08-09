import logging

import pytest

from agents.observability import observe_node


def test_observed_node_logs_completion(caplog) -> None:
    def node(state):
        return {"result": "ok"}

    state = {
        "execution_id": "test-observation-123",
    }

    with caplog.at_level(logging.INFO, logger="agents.observability"):
        result = observe_node("test_node", node)(state)

    assert result == {"result": "ok"}

    started = next(
        record
        for record in caplog.records
        if record.__dict__.get("event") == "node_started"
    )

    completed = next(
        record
        for record in caplog.records
        if record.__dict__.get("event") == "node_completed"
    )

    assert started.__dict__["execution_id"] == "test-observation-123"
    assert started.__dict__["node"] == "test_node"

    assert completed.__dict__["execution_id"] == "test-observation-123"
    assert completed.__dict__["node"] == "test_node"
    assert completed.__dict__["duration_ms"] >= 0


def test_observed_node_logs_failure_and_reraises(caplog) -> None:
    def node(state):
        raise RuntimeError("forced node failure")

    state = {
        "execution_id": "test-failed-node",
    }

    with caplog.at_level(logging.INFO, logger="agents.observability"):
        with pytest.raises(RuntimeError, match="forced node failure"):
            observe_node("failing_node", node)(state)

    failed = next(
        record
        for record in caplog.records
        if record.__dict__.get("event") == "node_failed"
    )

    assert failed.__dict__["execution_id"] == "test-failed-node"
    assert failed.__dict__["node"] == "failing_node"
    assert failed.__dict__["duration_ms"] >= 0