# Phase 6 Runtime Guide

## 1. What Was Created

### New files in this phase
- `tests/test_end_to_end_topics.py`
- `tests/test_determinism.py`
- `docs/phase_6_runtime.md`

### Updated files in this phase
- `src/simulated_city/mqtt.py`
  - Hardened `connect_mqtt(...)` with retry/backoff for startup-order resilience
- `docs/testing.md`
  - Added hardening checklist and Phase 6 test references
- `docs/setup.md`
  - Added recommended notebook startup order and troubleshooting

### Configuration changes
- No new `config.yaml` keys.
- Phase 6 tests rely on existing defaults:
  - roadwork blocked IDs `[44105317, 733901267]`
  - deterministic max ticks `600`

## 2. How to Run

1. Activate `.venv`.
2. Start local broker (`mosquitto`) and verify port `1883` is listening.
3. Run validation commands:
   ```bash
   python scripts/verify_setup.py
   python scripts/validate_structure.py
   python -m pytest
   ```
4. Run targeted hardening tests:
   ```bash
   python -m pytest tests/test_end_to_end_topics.py -v
   python -m pytest tests/test_determinism.py -v
   ```
5. Execute full notebook runbook (for manual reliability checks):
   - `agent_roadwork` publish cell
   - `agent_monitor` subscribe/process cells
   - `agent_cars` publish cell
   - `dashboard` subscribe/render cells
   - repeat cars+monitor updates twice and verify stable dashboard updates

## 3. Expected Output

### `tests/test_end_to_end_topics.py`
- Purpose: topic path and payload-contract smoke checks.
- Expected output:
  - pytest reports all tests in file as `PASSED`.
- Failure meaning:
  - Missing key assertion = notebook payload schema drift.
  - Topic mismatch assertion = topic helper naming drift.

### `tests/test_determinism.py`
- Purpose: repeat-run consistency and fixed scenario constraints.
- Exact expectations:
  - blocked IDs resolve to `(44105317, 733901267)`
  - `max_ticks == 600`
  - `success_rate >= 0.90`
  - two runs produce identical result dictionaries
- Failure meaning:
  - any mismatch indicates nondeterministic simulation inputs or config drift.

### Runtime behavior expectation for `connect_mqtt(...)`
- On transient startup timing issues, helper retries connection attempts automatically.
- If all attempts fail, it raises the last connection exception.

## 4. MQTT Topics (if changed/added)

- No new topics added in Phase 6.
- Existing topic contracts are validated by tests:
  - `simulated-city/city/roadwork/events`
  - `simulated-city/city/cars/telemetry`
  - `simulated-city/city/cars/reroute`
  - `simulated-city/city/traffic/congestion`

## 5. Debugging Guidance

- If full-suite tests fail intermittently:
  - rerun with local broker only (local profile active)
  - confirm notebook startup order from `docs/setup.md`
- If determinism test fails:
  - verify `config.yaml` blocked IDs and O-D pairs were not edited
  - verify no random runtime overrides are injected
- If topic contract test fails:
  - inspect payload keys in agent notebooks and align with required schema fields
- If MQTT connection fails:
  - check broker process status and `config.yaml` profile host/port
  - rerun after broker restarts; retry logic handles short startup delays

## 6. Verification Commands

```bash
python scripts/verify_setup.py
python scripts/validate_structure.py
python -m pytest
```
