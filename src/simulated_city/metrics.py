from __future__ import annotations


def count_cars_per_segment(telemetry_batch: list[dict]) -> dict[int, int]:
    """Count how many cars are reported on each segment in a telemetry batch."""

    counts: dict[int, int] = {}
    for event in telemetry_batch:
        segment_id = event.get("segment_id")
        if segment_id is None:
            continue
        segment_int = int(segment_id)
        counts[segment_int] = counts.get(segment_int, 0) + 1
    return counts


def update_congestion_streaks(
    cars_per_segment: dict[int, int],
    previous_streaks: dict[int, int],
    *,
    threshold: int = 10,
    required_ticks: int = 3,
) -> tuple[dict[int, int], list[int]]:
    """Update per-segment congestion streaks and return currently congested segments."""

    next_streaks: dict[int, int] = {}
    all_segments = set(previous_streaks) | set(cars_per_segment)

    for segment_id in all_segments:
        car_count = cars_per_segment.get(segment_id, 0)
        if car_count >= threshold:
            next_streaks[segment_id] = previous_streaks.get(segment_id, 0) + 1
        else:
            next_streaks[segment_id] = 0

    congested = [
        segment_id
        for segment_id, streak in sorted(next_streaks.items())
        if streak >= required_ticks
    ]
    return next_streaks, congested
