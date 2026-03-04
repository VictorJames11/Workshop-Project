# Phase 1 Runtime Guide

## 1. What Was Created

### Notebooks/Scripts
- `notebooks/agent_cars.ipynb` (current notebook includes MQTT + movement from later phases; still uses Phase 1 routing core)

### Library modules added in `src/simulated_city/`
- `src/simulated_city/routing.py`
  - `compute_reroute(...)`
  - `route_intersects_blocked_segments(...)`
  - `assign_od_pairs(...)`

### Configuration changes
- Updated `config.yaml` with:
  - `simulation.car_rerouting_phase1.seed`
  - `simulation.car_rerouting_phase1.max_ticks`
  - `simulation.car_rerouting_phase1.car_count`
  - `simulation.car_rerouting_phase1.blocked_segment_ids`
  - `simulation.car_rerouting_phase1.segment_node_pairs`
  - `simulation.car_rerouting_phase1.graph_adjacency`
  - `simulation.car_rerouting_phase1.od_pairs`
- Updated `src/simulated_city/config.py` to parse `simulation.car_rerouting_phase1` via `load_config()`.

## 2. How to Run

1. Open `notebooks/agent_cars.ipynb`.
2. Run cell 1 (markdown only).
3. Run cell 2 (config load and validation).
   - Observe output:
  - `Loaded Phase 4 config: seed=7, max_ticks=600, car_count=10`
  - `Default blocked segment IDs: [44105317]`
4. Run cell 3 (car O-D assignment and initial route build).
   - Observe output starts with:
  - `Built 10 cars with deterministic routes; ...`
5. Run cell 4 (multi-tick movement and reroute publishing).
   - Observe output:
  - `Tick <T> publish complete: telemetry=10, reroute_events=<N>, waiting=<W>, moving=<M>, arrived=<A>`
  - `Published ticks=<ticks_to_run>: telemetry=<N>, reroute_events=<N>`

If cell 4 output differs significantly (for example `waiting > 0`), see the debugging section.

## 3. Expected Output

### Cell 2 (load config)
- Purpose: confirm `load_config()` resolves Phase 1 settings.
- Exact expected lines:
  - `Loaded Phase 4 config: seed=7, max_ticks=600, car_count=10`
  - `Default blocked segment IDs: [44105317]`
- If different:
  - Missing line or exception means `simulation.car_rerouting_phase1` is missing or malformed in `config.yaml`.

### Cell 3 (build deterministic car routes)
- Purpose: create `car_count` cars with fixed O-D pairs and blocked-aware routes.
- Exact expected prefix:
  - `Built 10 cars with deterministic routes;`
- Expected sample shape:
  - list of dicts with keys: `car_id`, `origin`, `destination`, `route`, `status`
- If different:
  - `route: None` with many cars means graph data does not provide a valid path for those O-D pairs.

### Cell 4 (tick summary)
- Purpose: apply deterministic multi-tick movement and report per-tick outcomes.
- Exact expected lines:
  - `Tick <T> publish complete: telemetry=10, reroute_events=<N>, waiting=<W>, moving=<M>, arrived=<A>`
  - `Published ticks=<ticks_to_run>: telemetry=<N>, reroute_events=<N>`
- Success criteria:
  - per tick telemetry equals `car_count`.
- Failure criteria:
  - `waiting > 0` or runtime exceptions.

## 4. MQTT Topics (if applicable)

Current `agent_cars.ipynb` publishes and subscribes via MQTT as a Phase 4 superset.
- Published topics: `city/cars/telemetry`, `city/cars/reroute`
- Subscribed topics: `city/roadwork/events`, `city/traffic/congestion`

## 5. Debugging Guidance

### Increase verbosity
- In notebook cells, add temporary prints such as:
  - `print(phase1.graph_adjacency)`
  - `print(phase1.segment_node_pairs)`
  - `print(cars[:5])`

### Common errors and fixes
- Error: `Missing simulation.car_rerouting_phase1 in config.yaml`
  - Fix: ensure `config.yaml` contains `simulation.car_rerouting_phase1` section.
- Error about malformed mapping/list values
  - Fix: check these keys are correct YAML types:
    - `blocked_segment_ids` must be a list
    - `segment_node_pairs` must map segment ID -> two-node list
    - `graph_adjacency` must map node -> list of neighbors
    - `od_pairs` must be list of `{origin, destination}`
- Unexpected `waiting` count
  - Fix: verify each O-D pair has at least one path that avoids blocked segments.

### Verify simulation behavior
- Check that blocked segment `44105317` maps to `[N2, N3]`.
- Confirm reroutes use alternate path via `N4`/`N5` for `N1 -> N6`.

## 6. Verification Commands

```bash
python scripts/verify_setup.py
python scripts/validate_structure.py
python -m pytest
```
