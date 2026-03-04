# Configuration (`simulated_city.config`)

This module loads workshop configuration from:

- `config.yaml` (committed defaults, safe to share)
- optional `.env` (gitignored, for secrets like broker credentials)

It returns an `AppConfig` object that contains MQTT settings and optional simulation settings.


## Install

The base install already includes config support:

```bash
python -m pip install -e "."
```


## Data classes

### `MqttConfig`

Holds broker and topic settings.

Typical fields:

- `host`, `port`, `tls`
- `username`, `password` (usually loaded from environment variables)
- `client_id_prefix`, `keepalive_s`, `base_topic`


### `AppConfig`

Top-level config wrapper. Currently contains:

- `mqtt: MqttConfig`
- `mqtt_configs: dict[str, MqttConfig]` (all active MQTT profiles)
- `simulation: SimulationConfig | None`


### `SimulationConfig` (optional)

Simulation wrapper used by workshop notebooks.

For the rerouting workshop, this includes:

- `car_rerouting_phase1: CarReroutingPhase1Config | None`


### `CarReroutingPhase1Config`

Phase 2 expands these explicit fields so notebooks avoid hardcoded values:

- `seed`
- `tick_seconds`
- `max_ticks`
- `car_count`
- `blocked_segment_ids`
- `roadwork: CarReroutingRoadworkConfig`
- `routing: CarReroutingRoutingConfig`
- `segment_node_pairs`
- `graph_adjacency`
- `od_pairs`


### `CarReroutingRoadworkConfig`

- `start_tick` (default `180`)
- `end_tick` (default `300`)
- `blocked_segment_ids` (default includes `44105317` and `733901267`)


### `CarReroutingRoutingConfig`

- `reroute_cooldown_ticks` (default `3`)
- `base_edge_cost` (default `1.0`)
- `congestion_penalty` (default `2.0`)
- `tie_breaker` (default `node_id`)


## Functions

### `load_config(path="config.yaml") -> AppConfig`

Loads configuration, applying these rules:

1. Load `.env` from the current working directory if present.
2. Find `config.yaml`:
   - if `path` exists (or is absolute), use it
   - if `path` is a bare filename like `config.yaml`, search parent directories
     so notebooks in `notebooks/` still find the repo-root `config.yaml`
3. Read `mqtt.*` settings from YAML.
4. Optionally parse `simulation.*` settings from YAML.
5. Optionally read credentials from environment variables named in YAML:
   - `mqtt.username_env`
   - `mqtt.password_env`

Example:

```python
from simulated_city.config import load_config

cfg = load_config()
print(cfg.mqtt.host, cfg.mqtt.port, cfg.mqtt.tls)
print("base topic:", cfg.mqtt.base_topic)

if cfg.simulation and cfg.simulation.car_rerouting_phase1:
   phase1 = cfg.simulation.car_rerouting_phase1
   print("tick seconds:", phase1.tick_seconds)
   print("roadwork window:", phase1.roadwork.start_tick, phase1.roadwork.end_tick)
   print("routing cooldown:", phase1.routing.reroute_cooldown_ticks)
```


## Internal helpers (advanced)

These are used by `load_config()` and normally don’t need to be called directly:

- `_load_yaml_dict(path) -> dict`: reads a YAML mapping (or returns `{}`)
- `_resolve_default_config_path(path) -> Path`: notebook-friendly path resolution
