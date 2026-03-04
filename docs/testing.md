# Testing

This project uses `pytest` to validate configuration, MQTT helpers, routing logic, topic contracts, determinism, and map helpers.

## Run all checks

```bash
python scripts/verify_setup.py
python scripts/validate_structure.py
python -m pytest
```

## Phase 6 hardening tests

### `tests/test_end_to_end_topics.py`
Validates the cross-agent topic contract used by the distributed notebooks:
- `simulated-city/city/roadwork/events`
- `simulated-city/city/cars/telemetry`
- `simulated-city/city/cars/reroute`
- `simulated-city/city/traffic/congestion`

It checks required key presence for each payload schema so notebook agents stay compatible.

### `tests/test_determinism.py`
Runs a fixed rerouting scenario twice and verifies:
- identical outputs across runs
- fixed blocked IDs `(44105317, 733901267)`
- success-rate threshold (`>= 0.90`)
- expected `max_ticks` from config

## Targeted test runs

```bash
python -m pytest tests/test_end_to_end_topics.py -v
python -m pytest tests/test_determinism.py -v
python -m pytest tests/test_monitor_metrics.py -v
python -m pytest tests/test_mqtt_profiles.py -v
```

## Local broker notes

Some MQTT tests depend on broker availability and may skip if no broker is reachable.
Use local Mosquitto for stable workshop runs:

```bash
brew services start mosquitto
lsof -i :1883
```

## Troubleshooting

- If tests fail with connection timeouts, verify the active profile in `config.yaml` is local.
- If topic contract tests fail, align payload keys in agent notebooks with the required schemas.
- If determinism tests fail, re-check `config.yaml` roadwork blocked IDs and O-D setup.
- If structure validation warns, ensure each agent notebook keeps one-role-only responsibilities.
