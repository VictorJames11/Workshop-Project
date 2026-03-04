from simulated_city.config import load_config
from simulated_city.routing import assign_od_pairs, compute_reroute


SUCCESS_THRESHOLD = 0.90


def _run_phase_scenario() -> dict:
    cfg = load_config()
    assert cfg.simulation is not None
    phase = cfg.simulation.car_rerouting_phase1
    assert phase is not None

    assigned_pairs = assign_od_pairs(
        phase.car_count,
        [(item.origin, item.destination) for item in phase.od_pairs],
    )

    blocked = set(phase.roadwork.blocked_segment_ids)
    outcomes = []

    for origin, destination in assigned_pairs:
        route = compute_reroute(
            graph_adjacency=phase.graph_adjacency,
            origin=origin,
            destination=destination,
            blocked_segments=blocked,
            segment_node_pairs=phase.segment_node_pairs,
        )
        outcomes.append(route is not None)

    arrived = sum(1 for ok in outcomes if ok)
    success_rate = arrived / max(1, len(outcomes))

    return {
        "blocked": tuple(sorted(blocked)),
        "car_count": phase.car_count,
        "arrived": arrived,
        "success_rate": success_rate,
        "max_ticks": phase.max_ticks,
    }


def test_deterministic_phase_scenario_repeats_identically() -> None:
    first = _run_phase_scenario()
    second = _run_phase_scenario()

    assert first == second


def test_fixed_blocked_ids_and_success_threshold() -> None:
    result = _run_phase_scenario()

    assert result["blocked"] == (44105317, 733901267)
    assert result["max_ticks"] == 600
    assert result["success_rate"] >= SUCCESS_THRESHOLD
