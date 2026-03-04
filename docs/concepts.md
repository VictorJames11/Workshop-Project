# Concepts: Car Rerouting During Roadwork (Copenhagen)

This document clarifies the project design before implementation.

## 1) Trigger

- **Mobile entities:** Up to 30 homogeneous car agents.
- **State context:** Directed road graph of Copenhagen, per-edge status (`open`/`blocked`), simulation tick.
- **Activation event:** One or more road segments change to `blocked` due to roadwork, invalidating existing routes.

## 2) Observer

- **Inputs:** Roadwork status events and car telemetry (position/segment/speed).
- **Observed state:** Blocked edges, per-segment traffic load, and congestion indicators (for example low mean speed).
- **Output state:** Shared traffic snapshot for agents and dashboard.

## 3) Control Center

- **Decision loop:** At each tick, evaluate whether planned path intersects blocked segments.
- **Routing rule:** Recompute path on open subgraph; if multiple paths exist, choose by configured cost.
- **Failure rule:** If no feasible path exists, set car to waiting/retry state.
- **Congestion rule:** Mark segments congested when metric exceeds threshold.

## 4) Response

- **Action:** Affected cars switch route and continue movement with updated path.
- **System effect:** Traffic redistributes to detours; congestion may shift spatially.
- **Recovery:** When segments reopen, subsequent route plans may include them again.

## Expected Impact of Main-Road Blockages (Copenhagen)

When roadwork blocks major roads, you should expect a concentrated rerouting effect even with up to 30 cars:

- Many cars reroute within a short time window after the blockage starts.
- Traffic shifts to a small set of parallel or connector roads.
- Congestion appears on detour segments (authoritative rule: `cars_per_segment >= 10` for 3 consecutive ticks).
- Average trip time increases for routes that depend on the blocked corridor.
- Congestion reduces after blocked segments reopen and route options normalize.

These are baseline behavioral assumptions for interpreting simulation results.

## MQTT Topics (Publish/Subscribe)

Suggested minimal topic set:

- `city/roadwork/events`
  - **Publish:** Roadwork agent
  - **Subscribe:** Car agent, dashboard, monitor
- `city/cars/telemetry`
  - **Publish:** Car agent
  - **Subscribe:** Monitor, dashboard
- `city/cars/reroute`
  - **Publish:** Car agent
  - **Subscribe:** Dashboard, monitor
- `city/traffic/congestion`
  - **Publish:** Monitor agent
  - **Subscribe:** Car agent, dashboard
- `city/sim/tick` (optional)
  - **Publish:** Clock/coordinator agent
  - **Subscribe:** All agents

## Configuration Parameters

- **MQTT:** Host, port, TLS on/off, username env key, password env key, base topic, QoS.
- **Map/simulation area:** Copenhagen bounding box or center+radius, allowed road classes.
- **Vehicle model:** `car_count`, max speed, acceleration simplification, spawn policy.
- **Routing:** Replanning interval, reroute cooldown, primary route cost = distance; tie-breaker = lower `cars_per_segment`.
- **Roadwork:** Blocked segment IDs, start tick, end tick, number of concurrent closures.
- **Congestion:** Authoritative metric `cars_per_segment`; congested when count is >= 10 for 3 consecutive ticks. Keep `avg_speed` as diagnostic only.
- **Timing:** Tick duration (seconds), total simulation duration.

## Notebook Structure (One Notebook Per Agent Type)

- `notebooks/agent_roadwork.ipynb`
- `notebooks/agent_cars.ipynb`
- `notebooks/agent_monitor.ipynb`
- `notebooks/dashboard.ipynb` (anymap-ts)
- Optional: `notebooks/agent_clock.ipynb` for centralized tick events

## Classes vs Functions

### Good class candidates

- `CarState`, `RoadworkEvent`, `SegmentState`, `CongestionState` (data models)
- `CarAgentLogic` (route validity + reroute decisions)
- `TrafficMonitorLogic` (aggregation + threshold checks)

### Good function candidates

- Topic builders/parsers
- Metric calculations (mean speed, density)
- Route validity check helpers
- Payload validation/normalization

## Library Code vs Notebook Code

### `src/simulated_city/` (reusable library)

- Config loading/validation
- MQTT wrappers and publish checks
- Shared data models
- Routing/metric utilities
- Common constants/topic naming helpers

### Notebooks (scenario orchestration)

- Agent loops
- Simulation-specific parameters
- Subscriptions/publications wiring
- Visual presentation and interactive controls

## Decisions Made (Resolved Ambiguities)

1. **Rerouting mode:** Tick-driven.
2. **Authoritative congestion metric:** `cars_per_segment`.
  - A segment is congested when cars per segment is >= 10 for 3 consecutive ticks.
  - `avg_speed` is diagnostic only.
3. **Origin/destination generation:** Fixed list of predefined Copenhagen origin-destination pairs in v1 (no randomization).
4. **Arrival behavior:** Cars stop permanently at destination in v1 (no respawn).
  - Stop condition: simulation ends when all cars are stopped or `max_ticks` is reached.
5. **Road closure model:** Full block only in v1.
6. **Determinism:** Deterministic run with fixed seed for reproducibility.
7. **Success definition:**
  - Car success: encounters blocked route, reroutes to a valid alternative path, and reaches destination before `max_ticks`.
  - Simulation success: at least 90% of cars meet that condition in a run.
  - Secondary checks: report mean trip time increase and reroute count.
8. **MQTT profile strategy:** Use local profile as the default/fallback for reliable grading; cloud profile is optional.
9. **Roadwork timing (v1):** `start_tick = 180`, `end_tick = 300`, `duration = 120 ticks`.
10. **Route cost function (v1):**
   - Primary: shortest total path distance (sum of edge lengths), excluding blocked segments.
   - Tie-breaker: choose the route with lower current `cars_per_segment`.

## Blocked Segment Selection (Finalized)

- Decision scope: fixed IDs from major arterial roads (not random per run).
- v1 uses one blocked segment; v1.1 uses two.
- Fixed blocked-road IDs:
  - v1: `blocked_segment_ids: [44105317]` (H.C. Andersens Boulevard)
  - v1.1: `blocked_segment_ids: [44105317, 733901267]` (H.C. Andersens Boulevard + Vesterbrogade)
- Determinism rule: keep these IDs constant across runs.

## Realistic Starting Values

- `car_count`: 20 (scale to 30 later)
- `tick_seconds`: 1.0
- Simulation length: 600 ticks (10 minutes simulated)
- Concurrent blocked segments: 1-2
- Roadwork duration: 120 ticks
- Reroute cooldown: 5 ticks
- Count-based congestion: start with 8-12 cars/segment (tune by map size)

## Summary

The concept is coherent and workshop-appropriate. Core design decisions are now defined.

The concept is implementation-ready with fixed blocked-road IDs.
