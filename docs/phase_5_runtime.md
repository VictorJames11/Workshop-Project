# Phase 5 Runtime Guide

## 1. What Was Created

### New files in this phase
- `notebooks/dashboard.ipynb`
- `docs/phase_5_runtime.md`

### Updated files in this phase
- `src/simulated_city/maplibre_live.py`
  - Added `resolve_node_lnglat(...)`
  - Added `resolve_segment_lnglat(...)`
  - Added `car_popup_text(...)`
  - Added `DEFAULT_NODE_COORDINATES`
- `tests/test_maplibre_live.py`
  - Added helper sanity tests for Phase 5 dashboard helpers
- `docs/maplibre_anymap.md`
  - Added Phase 5 dashboard subscription/rendering guidance

### Configuration changes
- No `config.yaml` changes in this phase.
- Uses existing topic/config values and Phase 4 agents.

## 2. How to Run

1. Start local MQTT broker (Mosquitto) at `127.0.0.1:1883`.
2. Open and run `notebooks/agent_roadwork.ipynb` cells 1-3.
3. Open and run `notebooks/agent_monitor.ipynb` cells 1-3.
4. Open and run `notebooks/agent_cars.ipynb` cells 1-4.
5. Open and run `notebooks/dashboard.ipynb`:
   - Run cell 1 (title)
   - Run cell 2 (load config + connect + topic setup)
   - Run cell 3 (create map)
   - Run cell 4 (subscribe + redraw callback)
   - Run cell 5 (textual snapshot)
6. Re-run car/monitor publish cells as needed to stream updates and watch map markers update.
7. Run dashboard cell 6 to disconnect when done.

## 3. Expected Output

### `dashboard.ipynb` cell 2
- Purpose: connect MQTT and initialize state.
- Exact expected patterns:
  - `Connected MQTT target: 127.0.0.1:1883`
  - `Dashboard topics: telemetry=simulated-city/city/cars/telemetry, reroute=simulated-city/city/cars/reroute, roadwork=simulated-city/city/roadwork/events, congestion=simulated-city/city/traffic/congestion`
- If different:
  - Connection error/timeout means broker or profile mismatch.

### `dashboard.ipynb` cell 3
- Purpose: render anymap-ts map.
- Expected output:
  - Interactive map widget appears.
- If different:
  - Missing widget usually means kernel missing notebook extras installation.

### `dashboard.ipynb` cell 4
- Purpose: subscribe and activate async queue consumer for safe live redraw.
- Exact expected output:
  - `Dashboard subscriptions active with async queue consumer.`
- If different:
  - JSON decode errors indicate malformed payload on one of subscribed topics.

### `dashboard.ipynb` cell 5
- Purpose: textual snapshot for quick validation.
- Expected line patterns:
  - `Cars tracked: <int>`
  - `Reroute events tracked: <int>`
  - `Roadwork active: <bool> blocked=[...]`
  - `Congested segments: [...] (tick=<int>)`

### Visual expectations on map
- Blue markers (`#3388ff`) for cars using live telemetry coordinates (`current_lng`/`current_lat`) with `current_node` fallback.
- Red markers (`#d32f2f`) for blocked roadwork segments.
- Orange markers (`#ff9800`) for congested segments.

## 4. MQTT Topics (if changed/added)

Phase 5 adds dashboard subscriptions only; it does not publish new topics.

### Dashboard subscribed topics
- `simulated-city/city/roadwork/events`
- `simulated-city/city/cars/telemetry`
- `simulated-city/city/cars/reroute`
- `simulated-city/city/traffic/congestion`

### Dashboard published topics
- None (read-only visualization by design)

### Message schema assumptions used by dashboard
- Telemetry needs: `car_id`, `current_node`, `status`, `origin`, `destination`, `tick`
- Preferred live-position fields: `current_lng`, `current_lat`
- Roadwork needs: `active`, `blocked_segment_ids`
- Congestion needs: `congested_segment_ids`, `cars_per_segment`, `tick`

## 5. Debugging Guidance

- If map does not update:
  - Confirm dashboard cell 4 ran after cell 3.
  - Confirm other agents are publishing to the expected topics.
- If markers do not appear:
  - Check `current_lng`/`current_lat` or fallback `current_node` in telemetry.
  - Check segment IDs are present in `phase1.segment_node_pairs`.
- If dashboard throws key/JSON errors:
  - Validate payloads from car/roadwork/monitor notebooks are valid JSON.
- Use topic inspection in terminals:
  ```bash
  mosquitto_sub -h 127.0.0.1 -v -t "simulated-city/city/cars/telemetry"
  mosquitto_sub -h 127.0.0.1 -v -t "simulated-city/city/roadwork/events"
  mosquitto_sub -h 127.0.0.1 -v -t "simulated-city/city/traffic/congestion"
  ```

## 6. Verification Commands

```bash
python scripts/verify_setup.py
python scripts/validate_structure.py
python -m pytest
```
