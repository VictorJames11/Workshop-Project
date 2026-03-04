from simulated_city.routing import assign_od_pairs, compute_reroute, route_intersects_blocked_segments


def test_compute_reroute_avoids_blocked_segment() -> None:
    graph = {
        "N1": ("N2", "N4"),
        "N2": ("N1", "N3", "N5"),
        "N3": ("N2", "N6"),
        "N4": ("N1", "N5"),
        "N5": ("N4", "N2", "N6"),
        "N6": ("N3", "N5"),
    }
    segment_pairs = {
        44105317: ("N2", "N3"),
        733901267: ("N4", "N5"),
    }

    path = compute_reroute(
        graph_adjacency=graph,
        origin="N1",
        destination="N6",
        blocked_segments={44105317},
        segment_node_pairs=segment_pairs,
    )

    assert path is not None
    assert path[0] == "N1"
    assert path[-1] == "N6"
    assert route_intersects_blocked_segments(path, {44105317}, segment_pairs) is False


def test_route_intersects_blocked_segments_detects_overlap() -> None:
    route = ["N1", "N2", "N3", "N6"]
    blocked_segments = {44105317}
    segment_pairs = {44105317: ("N2", "N3")}

    assert route_intersects_blocked_segments(route, blocked_segments, segment_pairs) is True


def test_assign_od_pairs_repeats_deterministically() -> None:
    assigned = assign_od_pairs(
        car_count=5,
        od_pairs=[("N1", "N6"), ("N2", "N6")],
    )

    assert assigned == [
        ("N1", "N6"),
        ("N2", "N6"),
        ("N1", "N6"),
        ("N2", "N6"),
        ("N1", "N6"),
    ]
