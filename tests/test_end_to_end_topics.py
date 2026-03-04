from simulated_city.topics import (
    cars_reroute_topic,
    cars_telemetry_topic,
    roadwork_events_topic,
    traffic_congestion_topic,
)


def _require_keys(payload: dict, required_keys: set[str]) -> None:
    missing = required_keys - set(payload)
    assert not missing, f"Missing required keys: {sorted(missing)}"


def test_topic_paths_match_phase_contract() -> None:
    base = "simulated-city"
    assert cars_telemetry_topic(base) == "simulated-city/city/cars/telemetry"
    assert cars_reroute_topic(base) == "simulated-city/city/cars/reroute"
    assert roadwork_events_topic(base) == "simulated-city/city/roadwork/events"
    assert traffic_congestion_topic(base) == "simulated-city/city/traffic/congestion"


def test_phase_topic_payload_contracts_smoke() -> None:
    telemetry_payload = {
        "agent": "agent_cars",
        "tick": 1,
        "timestamp": "2026-01-01T00:00:01+00:00",
        "car_id": "car-01",
        "origin": "N1",
        "destination": "N6",
        "current_node": "N2",
        "segment_id": 44105317,
        "status": "arrived",
    }
    _require_keys(
        telemetry_payload,
        {
            "agent",
            "tick",
            "timestamp",
            "car_id",
            "origin",
            "destination",
            "current_node",
            "status",
        },
    )

    reroute_payload = {
        "agent": "agent_cars",
        "tick": 1,
        "timestamp": "2026-01-01T00:00:01+00:00",
        "car_id": "car-01",
        "origin": "N1",
        "destination": "N6",
        "old_route": ["N1", "N2", "N3", "N6"],
        "new_route": ["N1", "N4", "N5", "N6"],
        "blocked_segment_ids": [44105317, 733901267],
    }
    _require_keys(
        reroute_payload,
        {
            "agent",
            "tick",
            "timestamp",
            "car_id",
            "origin",
            "destination",
            "old_route",
            "new_route",
            "blocked_segment_ids",
        },
    )

    roadwork_payload = {
        "agent": "agent_roadwork",
        "tick": 180,
        "timestamp": "2026-01-01T00:03:00+00:00",
        "active": True,
        "blocked_segment_ids": [44105317, 733901267],
    }
    _require_keys(roadwork_payload, {"agent", "tick", "timestamp", "active", "blocked_segment_ids"})

    congestion_payload = {
        "agent": "agent_monitor",
        "tick": 3,
        "cars_per_segment": {"44105317": 12},
        "congested_segment_ids": [44105317],
        "roadwork_active": True,
        "blocked_segment_ids": [44105317, 733901267],
    }
    _require_keys(
        congestion_payload,
        {
            "agent",
            "tick",
            "cars_per_segment",
            "congested_segment_ids",
            "roadwork_active",
            "blocked_segment_ids",
        },
    )
