### Phase 1: Minimal working example (one agent, basic logic, no MQTT yet)
**Goal:** Build a deterministic, tick-driven single-agent notebook that demonstrates rerouting behavior against blocked roads without network communication.

**New Files:**
- notebooks/agent_cars.ipynb (notebook; initial single-agent loop scaffold)
- src/simulated_city/routing.py (library module; simple path validity and reroute helpers)
- tests/test_routing.py (test module; deterministic routing checks)

**Implementation Details:**
- Implement tick loop with deterministic seed and fixed origin/destination pairs.
- Apply full-block closure logic with fixed blocked segment IDs 44105317 and 733901267 (v1 runs with one ID active, second reserved for v1.1 scenario check).
- Recompute route when planned path intersects blocked segment; if no route exists, move to waiting/retry state.
- Keep congestion metric model as cars_per_segment conceptually defined, but defer MQTT-shared congestion state until later phases.
- Stop condition: all cars arrived or max_ticks reached.

**Dependencies:**
- No new package expected; use existing project dependencies only.

**Verification:**
- Commands to run: python scripts/verify_setup.py, python -m pytest, python scripts/validate_structure.py.
- Manual checks: run notebooks/agent_cars.ipynb, confirm reroute occurs when blocked segment is encountered, and confirm deterministic repeatability across runs.

**Investigation:**
- Validate that route helper design is simple and reusable for notebook agents.
- Confirm chosen fixed O-D pairs produce visible rerouting within 600 ticks.

### Phase 2: Add configuration file (config.yaml with MQTT and simulation parameters)
**Goal:** Move all simulation and MQTT-related parameters into configuration so notebooks avoid hardcoded values.

**New Files:**
- config.yaml (config file; expand simulation/roadwork/routing sections)
- src/simulated_city/config.py (library module; extend dataclasses/validation)
- tests/test_config.py (test module; add new config field coverage)
- docs/config.md (documentation; parameter reference updates)

**Implementation Details:**
- Add explicit settings for tick-driven simulation (tick_seconds, max_ticks), roadwork (start_tick=180, end_tick=300, blocked IDs), and routing (cooldown, cost/tie-breaker).
- Ensure local MQTT profile remains default/fallback and cloud profile optional.
- Keep fixed blocked IDs 44105317 and 733901267 in config defaults for deterministic grading.
- Maintain parent-directory config discovery behavior for notebooks.

**Dependencies:**
- No new package expected.

**Verification:**
- Commands to run: python scripts/verify_setup.py, python -m pytest, python scripts/validate_structure.py.
- Manual checks: load config from notebook directory, confirm defaults resolve correctly, and confirm single-agent notebook behavior matches Phase 1 with config-driven values.

**Investigation:**
- Review whether any config keys should be split into simulation, roadwork, and mqtt profiles for beginner clarity.
- Confirm .env-based credential resolution still works with local fallback.

### Phase 3: Add MQTT publishing (agent publishes to topics)
**Goal:** Enable the car agent notebook to publish telemetry and reroute events on MQTT while preserving deterministic tick logic.

**New Files:**
- notebooks/agent_cars.ipynb (notebook; add MQTT connect/publish)
- src/simulated_city/mqtt.py (library module; topic helpers if needed)
- src/simulated_city/topics.py (library module; optional centralized topic naming)
- tests/test_mqtt_profiles.py (test module; profile/default checks)
- docs/mqtt.md (documentation; publishing contract updates)

**Implementation Details:**
- Use connect_mqtt() with local profile default/fallback.
- Publish validated JSON via publish_json_checked() to city/cars/telemetry and city/cars/reroute.
- Emit events once per tick (or per state change where appropriate) with deterministic timestamps/tick fields.
- Keep one notebook per agent pattern intact (no monolithic combined notebook).

**Dependencies:**
- No new package expected if paho-mqtt is already present; otherwise add only required MQTT package in pyproject.toml.

**Verification:**
- Commands to run: python scripts/verify_setup.py, python -m pytest, python scripts/validate_structure.py.
- Manual checks: start local broker, run car notebook, verify messages appear on expected topics and payload schema is stable across repeated runs.

**Investigation:**
- Confirm publish frequency is beginner-friendly and does not spam unnecessary events.
- Validate minimal topic taxonomy before adding subscribers.

### Phase 4: Add second agent with MQTT subscription (agents communicate)
**Goal:** Introduce a monitor/roadwork agent pair so notebook agents communicate via MQTT subscriptions and shared topic contracts.

**New Files:**
- notebooks/agent_roadwork.ipynb (notebook; publishes roadwork events on schedule)
- notebooks/agent_monitor.ipynb (notebook; subscribes, aggregates congestion)
- src/simulated_city/metrics.py (library module; congestion counters and streak logic)
- tests/test_monitor_metrics.py (test module; cars_per_segment >= 10 for 3 ticks rule)
- docs/exercises.md (documentation; multi-notebook run sequence)

**Implementation Details:**
- Roadwork agent publishes closures for fixed IDs 44105317 and 733901267 according to configured tick windows.
- Monitor subscribes to telemetry and roadwork events, computes authoritative congestion (cars_per_segment) and publishes city/traffic/congestion.
- Car agent subscribes to roadwork/congestion topics and applies reroute cooldown behavior.
- Keep architecture distributed: each agent runs in its own notebook and communicates only through MQTT.

**Dependencies:**
- No new package expected.

**Verification:**
- Commands to run: python scripts/verify_setup.py, python -m pytest, python scripts/validate_structure.py.
- Manual checks: run roadwork, car, and monitor notebooks together; confirm congestion events fire only after 3-tick threshold streak and reroute events reflect incoming roadwork updates.

**Investigation:**
- Check whether optional centralized clock notebook is required now or can remain deferred.
- Validate ordering assumptions when multiple notebooks start at slightly different times.

### Phase 5: Add dashboard visualization (anymap-ts)
**Goal:** Build a dashboard notebook that subscribes to agent outputs and visualizes live state with anymap-ts only.

**New Files:**
- notebooks/dashboard.ipynb (notebook; visualization and subscriptions)
- src/simulated_city/maplibre_live.py (library module; anymap-ts integration helpers)
- tests/test_maplibre_live.py (test module; dashboard helper sanity)
- docs/maplibre_anymap.md (documentation; usage and constraints)

**Implementation Details:**
- Subscribe dashboard to city/roadwork/events, city/cars/telemetry, city/cars/reroute, and city/traffic/congestion.
- Render car positions, blocked segments, and congestion overlays using anymap-ts primitives.
- Keep visualization read-only and event-driven from MQTT messages.
- Preserve one notebook per agent design and avoid introducing non-approved plotting stacks.

**Dependencies:**
- Ensure anymap-ts[all] is present in pyproject.toml; do not add folium/plotly/matplotlib.

**Verification:**
- Commands to run: python scripts/verify_setup.py, python -m pytest, python scripts/validate_structure.py.
- Manual checks: run all agent notebooks plus dashboard, verify live updates for closures/reroutes/congestion, and confirm no unsupported mapping library usage.

**Investigation:**
- Verify map update cadence is smooth enough for workshops without adding complexity.
- Confirm dashboard remains robust when a publisher temporarily disconnects.

### Phase 6: Hardening
**Goal:** Stabilize reliability, teachability, and validation so the full distributed simulation is reproducible and workshop-ready.

**New Files:**
- tests/test_end_to_end_topics.py (test module; topic contract smoke tests)
- tests/test_determinism.py (test module; repeat-run consistency checks)
- docs/testing.md (documentation; hardening checklist and troubleshooting)
- docs/setup.md (documentation; local broker and run-order clarifications)

**Implementation Details:**
- Add lightweight contract checks for required topic fields and phase-aligned payload schemas.
- Add deterministic scenario test validating fixed blocked IDs and expected reroute success threshold behavior.
- Improve reconnect/retry behavior for local MQTT fallback and notebook startup ordering.
- Finalize runbook: recommended notebook startup order, manual validation path, and expected outputs.

**Dependencies:**
- Prefer no new packages; add only minimal test dependency if strictly necessary and aligned with current toolchain.

**Verification:**
- Commands to run: python scripts/verify_setup.py, python -m pytest, python scripts/validate_structure.py.
- Manual checks: full-system run with local broker default profile, confirm all notebooks interoperate, and verify reproducible outputs across two consecutive runs.

**Investigation:**
- Identify any remaining flaky behaviors under local-only workshop environments.
- Confirm documentation and tests are sufficient for first-time students to complete setup and phased execution without instructor intervention.
