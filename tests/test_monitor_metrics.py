from simulated_city.metrics import count_cars_per_segment, update_congestion_streaks


def test_count_cars_per_segment_counts_only_present_segment_ids() -> None:
    telemetry = [
        {"car_id": "car-01", "segment_id": 44105317},
        {"car_id": "car-02", "segment_id": 44105317},
        {"car_id": "car-03", "segment_id": 733901267},
        {"car_id": "car-04", "segment_id": None},
    ]

    assert count_cars_per_segment(telemetry) == {
        44105317: 2,
        733901267: 1,
    }


def test_update_congestion_streaks_requires_three_ticks_at_threshold() -> None:
    streaks = {}

    streaks, congested = update_congestion_streaks({44105317: 10}, streaks, threshold=10, required_ticks=3)
    assert congested == []

    streaks, congested = update_congestion_streaks({44105317: 12}, streaks, threshold=10, required_ticks=3)
    assert congested == []

    streaks, congested = update_congestion_streaks({44105317: 11}, streaks, threshold=10, required_ticks=3)
    assert congested == [44105317]


def test_update_congestion_streaks_resets_when_below_threshold() -> None:
    streaks = {44105317: 2}

    streaks, congested = update_congestion_streaks({44105317: 8}, streaks, threshold=10, required_ticks=3)

    assert streaks[44105317] == 0
    assert congested == []
