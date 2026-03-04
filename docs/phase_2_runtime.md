# Phase 2 Runtime Guide

## 1. What Was Created

### New/Updated files in this phase
- Updated `config.yaml`
  - Added explicit Phase 2 settings under `simulation.car_rerouting_phase1` for:
    - `tick_seconds`
    - `roadwork.start_tick`, `roadwork.end_tick`, `roadwork.blocked_segment_ids`
    - `routing.reroute_cooldown_ticks`, `routing.base_edge_cost`, `routing.congestion_penalty`, `routing.tie_breaker`
- Updated `src/simulated_city/config.py`
  - Added structured config parsing for Phase 2 fields:
    - `CarReroutingRoadworkConfig`
    - `CarReroutingRoutingConfig`
    - `tick_seconds` support in `CarReroutingPhase1Config`
- Updated `tests/test_config.py`
  - Added coverage for explicit Phase 2 values and default fallback behavior.
- Updated `docs/config.md`
  - Added parameter reference and usage examples for Phase 2 config fields.

### Previous phase artifacts used (unchanged)
- `notebooks/agent_cars.ipynb`
- `src/simulated_city/routing.py`
- `tests/test_routing.py`
- `docs/phase_1_runtime.md`

## 2. How to Run

1. From project root, run setup/validation commands:
   ```bash
   /Users/christinathomasvictor/Documents/Workshop-Project/.venv/bin/python scripts/verify_setup.py
   /Users/christinathomasvictor/Documents/Workshop-Project/.venv/bin/python scripts/validate_structure.py
   /Users/christinathomasvictor/Documents/Workshop-Project/.venv/bin/python -m pytest
   ```
2. Open `notebooks/agent_cars.ipynb`.
3. Run cell 2 (load config).
   - This confirms config parsing is still valid with new Phase 2 fields.
4. Run cell 3 and cell 4.
  - Behavior follows current moving Phase 4 notebook, while still validating Phase 2 config fields.

## 3. Expected Output

### Notebook cell 2 (`notebooks/agent_cars.ipynb`)
- Purpose: verify `load_config()` with expanded Phase 2 schema.
- Exact expected output lines:
  - `Loaded Phase 4 config: seed=7, max_ticks=600, car_count=10`
  - `Default blocked segment IDs: [44105317]`
- If output differs:
  - Missing first line: config parsing failed.
  - Missing blocked IDs line: `simulation.car_rerouting_phase1.blocked_segment_ids` malformed.

### Notebook cell 3
- Purpose: deterministic car initialization using parsed config.
- Expected prefix:
  - `Built 10 cars with deterministic routes;`
- If output differs:
  - Fewer than 10 cars indicates invalid `car_count` or O-D config shape.

### Notebook cell 4
- Purpose: deterministic multi-tick movement summary.
- Exact expected lines include:
  - `Tick <T> publish complete: telemetry=10, reroute_events=<N>, waiting=<W>, moving=<M>, arrived=<A>`
  - `Published ticks=<ticks_to_run>: telemetry=<N>, reroute_events=<N>`
- If output differs:
  - persistent `waiting > 0` indicates graph/segment config inconsistency or fully blocked routes.

### Test outputs
- `pytest` should include passing new tests:
  - `test_load_config_parses_phase2_car_rerouting_settings`
  - `test_load_config_phase2_defaults_for_roadwork_and_routing`

## 4. MQTT Topics (if changed/added)

Current `agent_cars.ipynb` includes MQTT publish/subscribe behavior from later phases.
- Topics published: cars telemetry/reroute
- Topics subscribed: roadwork events/traffic congestion

## 5. Debugging Guidance

### Config-type validation errors
- Error: `simulation.car_rerouting_phase1.roadwork must be a mapping`
  - Fix: ensure `roadwork:` is YAML mapping, not list/string.
- Error: `...blocked_segment_ids must be a list`
  - Fix: set as list, e.g. `[44105317, 733901267]`.
- Error on routing mapping
  - Fix: ensure `routing:` contains scalar values:
    - `reroute_cooldown_ticks: 3`
    - `base_edge_cost: 1.0`
    - `congestion_penalty: 2.0`
    - `tie_breaker: "node_id"`

### Verify current loaded values quickly
Use this one-liner in notebook or REPL:
```python
from simulated_city.config import load_config
p = load_config().simulation.car_rerouting_phase1
print(p.tick_seconds, p.roadwork.start_tick, p.roadwork.end_tick, p.routing.reroute_cooldown_ticks)
```
Expected printed values with current defaults:
- `1.0 180 300 3`

## 6. Verification Commands

```bash
python scripts/verify_setup.py
python scripts/validate_structure.py
python -m pytest
```
