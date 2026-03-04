# Phase 4 Runtime Guide

## 1. What Was Created

### New files in this phase
- `notebooks/agent_roadwork.ipynb`
- `notebooks/agent_monitor.ipynb`
- `src/simulated_city/metrics.py`
- `tests/test_monitor_metrics.py`

### Updated files in this phase
- `notebooks/agent_cars.ipynb` (per-tick movement + live rerouting)
- `src/simulated_city/topics.py` (roadwork/congestion topic helpers)

## 2. How to Run

1. Start local broker (Mosquitto).
2. Run `notebooks/agent_roadwork.ipynb` cells 1-3.
3. Run `notebooks/agent_monitor.ipynb` cells 1-2 (leave connected).
4. Run `notebooks/agent_cars.ipynb` cells 1-4.
5. Run `notebooks/agent_monitor.ipynb` cell 3 (publish congestion).
6. Re-run `notebooks/agent_cars.ipynb` cell 4 to consume latest congestion/roadwork state.
7. Disconnect monitor (cell 4) when done.

## 3. Expected Output

### `agent_cars.ipynb`
- Cell 2 prints the loaded config and topic names, including roadwork/congestion input topics.
- Cell 4 prints one summary per tick:
  - `Tick <T> publish complete: telemetry=<car_count>, reroute_events=<N>, waiting=<W>, moving=<M>, arrived=<A>`
  - `Published ticks=<ticks_to_run>: telemetry=<car_count * ticks_to_run>, reroute_events=<N>`

Current default from `config.yaml`:
- `car_count = 10`
- per tick telemetry is `10`.

### `agent_monitor.ipynb`
- Cell 3 prints:
  - `Published congestion tick=<T>: segments={<segment>: <count>, ...}, congested=[...]`

## 4. MQTT Topics

### Published
- `simulated-city/city/roadwork/events` (roadwork agent)
- `simulated-city/city/cars/telemetry` (cars agent)
- `simulated-city/city/cars/reroute` (cars agent)
- `simulated-city/city/traffic/congestion` (monitor agent)

### Subscribed
- `agent_cars.ipynb` subscribes to:
  - `simulated-city/city/roadwork/events`
  - `simulated-city/city/traffic/congestion`
- `agent_monitor.ipynb` subscribes to:
  - `simulated-city/city/cars/telemetry`
  - `simulated-city/city/roadwork/events`

## 5. Debugging Guidance

- If cars cluster, confirm telemetry contains `current_lng` and `current_lat`.
- If rerouting is missing, run roadwork publish first, then re-run cars cell 4.
- If no congestion appears, run monitor cell 3 after enough telemetry ticks.

## 6. Verification Commands

```bash
python scripts/verify_setup.py
python scripts/validate_structure.py
python -m pytest
```
