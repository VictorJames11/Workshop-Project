# Setup

This workshop targets Python `>=3.11`.

## 1) Create and activate virtual environment

macOS/Linux:

```bash
python3 scripts/create_venv.py
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -e ".[dev,notebooks]"

# If GDAL/raster dependencies fail, use the no-GDAL notebook install:
python -m pip install -e ".[dev]"
python -m pip install "jupyterlab>=4" "ipykernel>=6" "anymap-ts"
```

Windows PowerShell:

```powershell
python scripts/create_venv.py
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
python -m pip install -e ".[dev,notebooks]"

# If GDAL/raster dependencies fail, use the no-GDAL notebook install:
python -m pip install -e ".[dev]"
python -m pip install "jupyterlab>=4" "ipykernel>=6" "anymap-ts"
```

## 2) Verify environment

```bash
python scripts/verify_setup.py
python scripts/validate_structure.py
python -m pytest
```

## 3) Start local MQTT broker (recommended)

macOS (Homebrew):

```bash
brew install mosquitto
brew services start mosquitto
lsof -i :1883
```

Use local profile in `config.yaml` for reproducible workshop runs.

If Homebrew Mosquitto is not available on your macOS version, run a minimal Docker broker instead:

```bash
docker run -d --name simcity-mosquitto -p 1883:1883 eclipse-mosquitto:2
docker ps --filter name=simcity-mosquitto
```

Stop and remove when done:

```bash
docker stop simcity-mosquitto
docker rm simcity-mosquitto
```

Minimum needed for this Docker fallback:
- A working Docker runtime (`docker` CLI command available)
- CPU virtualization support enabled
- At least 2 CPU cores and 4 GB RAM (8 GB recommended)
- About 2 GB free disk space
- In `config.yaml`, use `active_profiles: [local]` with host `127.0.0.1`, port `1883`, and `tls: false`

If Docker Desktop is unsupported on an older macOS release, use Docker CLI with Colima:

```bash
brew install docker colima
colima start --cpu 2 --memory 4 --disk 20
docker run -d --name simcity-mosquitto -p 1883:1883 eclipse-mosquitto:2
```

## 4) Recommended notebook startup order (Phase 6 runbook)

For stable distributed behavior, start notebooks in this order:

1. `notebooks/agent_roadwork.ipynb` (run publish cell)
2. `notebooks/agent_monitor.ipynb` (run subscribe cell, then process cell)
3. `notebooks/agent_cars.ipynb` (run connect/build/publish cells)
4. `notebooks/dashboard.ipynb` (run connect/map/subscribe cells)

Then iterate:
- run cars publish cell
- run monitor process cell
- observe dashboard update

This order reduces startup races and makes messages visible immediately.

## 5) Quick troubleshooting

- `TimeoutError` on MQTT connect:
  - confirm broker is running at `127.0.0.1:1883`
  - confirm active profile is local in `config.yaml`
- Publish verification timeout:
  - rerun the notebook cell after broker is stable
  - avoid disconnecting before publish completes
- Missing dashboard updates:
  - rerun dashboard subscribe cell after other agents are connected

## 6) Optional install fallback (new Python versions)

If geospatial extras fail to build on very new Python versions:

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -e ".[dev]"
python -m pip install "jupyterlab>=4" "ipykernel>=6" "anymap-ts"
```

Then run:

```bash
python scripts/verify_setup.py
```
