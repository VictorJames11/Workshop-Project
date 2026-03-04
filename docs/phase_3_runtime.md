# Phase 3 Runtime Guide

## 1. What Was Created

### New/Updated files in this phase
- Updated `notebooks/agent_cars.ipynb`
  - Added MQTT connection via `connect_mqtt(config.mqtt)`
  - Added topic setup using `src/simulated_city/topics.py`
  - Added verified publishing with `publish_json_checked(...)` for telemetry and reroute events
- Updated `src/simulated_city/mqtt.py`
  - Added `connect_mqtt(...)`
  - Added `publish_json_checked(...)`
- Added `src/simulated_city/topics.py`
  - `cars_telemetry_topic(base_topic)`
  - `cars_reroute_topic(base_topic)`
- Updated `tests/test_mqtt_profiles.py`
  - Added unit checks for `connect_mqtt` and `publish_json_checked`
- Updated `docs/mqtt.md`
  - Added helper API usage and Phase 3 topic/payload contract

### Previous phase artifacts used (unchanged)
- `config.yaml` (Phase 2 config schema retained)
- `src/simulated_city/config.py`
- `src/simulated_city/routing.py`
- `tests/test_routing.py`
- `docs/phase_1_runtime.md`
- `docs/phase_2_runtime.md`

## 2. How to Run

### Workflow A: Run car agent notebook
1. Start your local broker (for example Mosquitto on `127.0.0.1:1883`).
2. Open `notebooks/agent_cars.ipynb`.
3. Run cell 1 (markdown intro).
4. Run cell 2.
   - Expected: configuration load + MQTT connection + topic printout.
5. Run cell 3.
   - Expected: deterministic car state creation.
6. Run cell 4.
   - Expected: per-car telemetry publishing + reroute event publishing + clean disconnect.

### Workflow B: Observe messages while notebook runs
1. In terminal, subscribe to telemetry:
   ```bash
   mosquitto_sub -h 127.0.0.1 -v -t "simulated-city/city/cars/telemetry"
   ```
2. In another terminal, subscribe to reroute events:
   ```bash
   mosquitto_sub -h 127.0.0.1 -v -t "simulated-city/city/cars/reroute"
   ```
3. Run notebook cells 2, 3, 4.
4. Observe live JSON messages in both terminal subscribers.

## 3. Expected Output

### Cell 2 (connect and topics)
- Purpose: load config + connect MQTT + build topic names.
- Exact output patterns:
  - `Loaded Phase 4 config: seed=7, max_ticks=600, car_count=10`
  - `Default blocked segment IDs: [44105317]`
  - `Roadwork input topic: simulated-city/city/roadwork/events`
  - `Congestion input topic: simulated-city/city/traffic/congestion`
  - `Connected MQTT target: 127.0.0.1:1883`
  - `Publish topics: telemetry=simulated-city/city/cars/telemetry, reroute=simulated-city/city/cars/reroute`
- If different:
  - Connection timeout/error means broker is not reachable or wrong profile is active.

### Cell 3 (car state)
- Purpose: build deterministic planned route vs active route.
- Exact output prefix:
  - `Built 10 cars with deterministic routes; initial_reroute_candidates=`
  - `Sample entries:`
- If different:
  - Missing cars or `route: None` indicates graph/OD mismatch in config.

### Cell 4 (publishing)
- Purpose: publish per-tick moving telemetry and reroute events while reacting to live traffic inputs.
- Exact output pattern:
  - `Tick <T> publish complete: telemetry=10, reroute_events=<N>, waiting=<W>, moving=<M>, arrived=<A>`
  - `Published ticks=<ticks_to_run>: telemetry=<N>, reroute_events=<N>`
  - `Disconnected MQTT client.`
- Expected values with current config:
  - `telemetry=10` per tick
  - `reroute_events` is at least `1` when blocked edges affect at least one route
- Success criteria:
  - No exceptions, output printed, and subscriber terminals receive JSON payloads.

## 4. MQTT Topics (changed/added)

### Published topics
- `simulated-city/city/cars/telemetry`
  - Notebook: `notebooks/agent_cars.ipynb`
  - Data schema:
    - `agent` (str)
    - `tick` (int)
    - `timestamp` (ISO-8601 str)
    - `car_id` (str)
    - `origin` (str)
    - `destination` (str)
    - `current_node` (str)
    - `status` ("arrived" | "waiting")

- `simulated-city/city/cars/reroute`
  - Notebook: `notebooks/agent_cars.ipynb`
  - Data schema:
    - `agent` (str)
    - `tick` (int)
    - `timestamp` (ISO-8601 str)
    - `car_id` (str)
    - `origin` (str)
    - `destination` (str)
    - `old_route` (list[str] | null)
    - `new_route` (list[str])
    - `blocked_segment_ids` (list[int])

### Subscribed topics
- Current `agent_cars.ipynb` also subscribes to:
  - `simulated-city/city/roadwork/events`
  - `simulated-city/city/traffic/congestion`

## 5. Debugging Guidance

### Enable more detail in notebook
- Add temporary prints in cell 4:
  - `print(telemetry_payload)`
  - `print(reroute_payload)`

### Common errors and solutions
- `TimeoutError: Could not connect to MQTT broker ...`
  - Ensure local broker is running on host/port from `config.yaml` active profile.
- `RuntimeError: Publish verification timed out for topic ...`
  - Ensure broker allows self-subscribe loopback and notebook remains connected.
  - Verify no firewall blocks local broker traffic.
- Unexpected topic path
  - Check `mqtt.base_topic` in `config.yaml`; topic suffixes are always `city/cars/telemetry` and `city/cars/reroute`.

### Verify message flow
- Use two `mosquitto_sub` terminals from Workflow B.
- Confirm telemetry count equals notebook `telemetry` value.
- Confirm reroute events appear only when `was_rerouted` is true.

## 6. Verification Commands

```bash
python scripts/verify_setup.py
python scripts/validate_structure.py
python -m pytest
```
