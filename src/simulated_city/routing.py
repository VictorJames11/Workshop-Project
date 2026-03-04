from __future__ import annotations

from collections import deque
from typing import Iterable


def route_intersects_blocked_segments(
    route_nodes: list[str],
    blocked_segments: set[int],
    segment_node_pairs: dict[int, tuple[str, str]],
) -> bool:
    """Return True when a node route traverses at least one blocked segment."""

    traversed_edges = {
        frozenset((route_nodes[index], route_nodes[index + 1]))
        for index in range(len(route_nodes) - 1)
    }

    for segment_id in blocked_segments:
        edge = segment_node_pairs.get(segment_id)
        if edge is None:
            continue
        if frozenset(edge) in traversed_edges:
            return True

    return False


def compute_reroute(
    graph_adjacency: dict[str, tuple[str, ...]],
    origin: str,
    destination: str,
    blocked_segments: set[int],
    segment_node_pairs: dict[int, tuple[str, str]],
) -> list[str] | None:
    """Compute shortest-by-hops path while avoiding blocked segments."""

    if origin == destination:
        return [origin]

    blocked_edges = {
        frozenset(segment_node_pairs[segment_id])
        for segment_id in blocked_segments
        if segment_id in segment_node_pairs
    }

    queue: deque[tuple[str, list[str]]] = deque([(origin, [origin])])
    visited = {origin}

    while queue:
        current_node, path = queue.popleft()

        for neighbor in graph_adjacency.get(current_node, ()):
            if frozenset((current_node, neighbor)) in blocked_edges:
                continue

            if neighbor == destination:
                return [*path, neighbor]

            if neighbor in visited:
                continue

            visited.add(neighbor)
            queue.append((neighbor, [*path, neighbor]))

    return None


def assign_od_pairs(car_count: int, od_pairs: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    """Assign O-D pairs to cars by repeating the fixed list deterministically."""

    base_pairs = list(od_pairs)
    if not base_pairs:
        raise ValueError("At least one O-D pair is required")

    return [base_pairs[index % len(base_pairs)] for index in range(car_count)]
