from __future__ import annotations


def _join_topic(base_topic: str, *segments: str) -> str:
    cleaned = [base_topic.strip("/")]
    cleaned.extend(segment.strip("/") for segment in segments)
    return "/".join(part for part in cleaned if part)


def cars_telemetry_topic(base_topic: str) -> str:
    """Topic for per-tick car telemetry events."""

    return _join_topic(base_topic, "city", "cars", "telemetry")


def cars_reroute_topic(base_topic: str) -> str:
    """Topic for reroute events emitted by the car agent."""

    return _join_topic(base_topic, "city", "cars", "reroute")


def roadwork_events_topic(base_topic: str) -> str:
    """Topic for roadwork closure events."""

    return _join_topic(base_topic, "city", "roadwork", "events")


def traffic_congestion_topic(base_topic: str) -> str:
    """Topic for authoritative congestion events from monitor."""

    return _join_topic(base_topic, "city", "traffic", "congestion")
