from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import yaml


@dataclass(frozen=True, slots=True)
class MqttConfig:
    host: str
    port: int
    tls: bool
    username: str | None
    password: str | None = field(repr=False)
    client_id_prefix: str
    keepalive_s: int
    base_topic: str


@dataclass(frozen=True, slots=True)
class AppConfig:
    mqtt: MqttConfig  # Primary (first active) MQTT broker
    mqtt_configs: dict[str, MqttConfig] = field(default_factory=dict)  # All active profiles
    simulation: "SimulationConfig | None" = None


@dataclass(frozen=True, slots=True)
class SimulationLocationConfig:
    location_id: str
    lat: float
    lon: float


@dataclass(frozen=True, slots=True)
class CarReroutingOdPair:
    origin: str
    destination: str


@dataclass(frozen=True, slots=True)
class CarReroutingRoadworkConfig:
    start_tick: int = 180
    end_tick: int = 300
    blocked_segment_ids: tuple[int, ...] = (44105317, 733901267)


@dataclass(frozen=True, slots=True)
class CarReroutingRoutingConfig:
    reroute_cooldown_ticks: int = 3
    base_edge_cost: float = 1.0
    congestion_penalty: float = 2.0
    tie_breaker: str = "node_id"


@dataclass(frozen=True, slots=True)
class CarReroutingPhase1Config:
    seed: int = 7
    tick_seconds: float = 1.0
    max_ticks: int = 600
    car_count: int = 20
    blocked_segment_ids: tuple[int, ...] = ()
    roadwork: CarReroutingRoadworkConfig = field(default_factory=CarReroutingRoadworkConfig)
    routing: CarReroutingRoutingConfig = field(default_factory=CarReroutingRoutingConfig)
    segment_node_pairs: dict[int, tuple[str, str]] = field(default_factory=dict)
    graph_adjacency: dict[str, tuple[str, ...]] = field(default_factory=dict)
    od_pairs: tuple[CarReroutingOdPair, ...] = ()


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Configuration for the rubbish-bin simulation.

    Notes
    - This section is optional; the template can be used without any simulation.
    - We keep the config immutable (frozen dataclasses) so it behaves like a
      simple value object.
    """

    timestep_minutes: int = 15
    arrival_prob: float = 0.25
    bag_fill_delta_pct: int = 2
    status_boundary_pct: int = 10
    # If true, emit a status event on every successful deposit (more frequent).
    # If false, emit only when crossing each N% boundary.
    publish_every_deposit: bool = False
    step_delay_s: float = 0.0
    # Optional: fixed simulation start timestamp (UTC) for deterministic logs.
    # If None, the simulator uses the current wall-clock time.
    start_time: datetime | None = None
    seed: int | None = None
    locations: tuple[SimulationLocationConfig, ...] = ()
    car_rerouting_phase1: CarReroutingPhase1Config | None = None


def _parse_utc_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        s = value.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
    else:
        raise ValueError("simulation.start_time must be an ISO-8601 datetime string")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    # Load a local .env if present (it is gitignored by default).
    # This makes workshop setup easier while keeping secrets out of git.
    load_dotenv(override=False)

    resolved_path = _resolve_default_config_path(path)
    data = _load_yaml_dict(resolved_path)
    active_profiles = _get_active_profiles(data)
    mqtt_config_dicts = _load_mqtt_configs(data, active_profiles)
    simulation = data.get("simulation")

    # Build MqttConfig objects for all active profiles
    mqtt_configs: dict[str, MqttConfig] = {}
    primary_mqtt = None

    for profile_name, mqtt_dict in mqtt_config_dicts.items():
        mqtt_config = _dict_to_mqtt_config(mqtt_dict)
        mqtt_configs[profile_name] = mqtt_config
        if primary_mqtt is None:
            primary_mqtt = mqtt_config

    if primary_mqtt is None:
        raise ValueError("No active MQTT profiles found in config")

    sim_cfg = _parse_simulation_config(simulation)

    return AppConfig(
        mqtt=primary_mqtt,
        mqtt_configs=mqtt_configs,
        simulation=sim_cfg,
    )


def _select_mqtt_config(data: dict[str, Any]) -> dict[str, Any]:
    """Return the effective MQTT config mapping.

    Supported YAML shapes:

    1) Legacy (single broker):
       mqtt: {host, port, tls, ...}

    2) Profile-based:
       mqtt:
         profile: local
         profiles:
           local: {host, port, tls, ...}
           other: {...}

    The active profile can also be selected via env var:
    - SIMCITY_MQTT_PROFILE (preferred)
    - MQTT_PROFILE (fallback)
    """

    raw = data.get("mqtt") or {}
    if not isinstance(raw, dict):
        raise ValueError("Config key 'mqtt' must be a mapping")

    profiles = raw.get("profiles")
    if profiles is None:
        return raw
    if not isinstance(profiles, dict):
        raise ValueError("Config key 'mqtt.profiles' must be a mapping")

    env_profile = os.getenv("SIMCITY_MQTT_PROFILE") or os.getenv("MQTT_PROFILE")
    profile_name = env_profile or raw.get("profile") or raw.get("active_profile") or raw.get("default_profile")

    if not profile_name:
        # Sensible default: prefer a profile named 'local' if present.
        profile_name = "local" if "local" in profiles else next(iter(profiles.keys()), None)

    if not profile_name:
        raise ValueError("Config key 'mqtt.profiles' is empty; define at least one profile")

    if profile_name not in profiles:
        available = ", ".join(sorted(str(k) for k in profiles.keys()))
        raise ValueError(f"Unknown MQTT profile '{profile_name}'. Available: {available}")

    selected = profiles.get(profile_name) or {}
    if not isinstance(selected, dict):
        raise ValueError(f"Config key 'mqtt.profiles.{profile_name}' must be a mapping")

    # Merge: common mqtt settings first, then profile overrides.
    common: dict[str, Any] = {
        k: v
        for k, v in raw.items()
        if k not in {"profiles", "profile", "active_profile", "default_profile"}
    }
    return {**common, **selected}


def _get_active_profiles(data: dict[str, Any]) -> list[str]:
    """Return the list of active MQTT profile names.
    
    Supports:
    1) active_profiles: [local, mqtthq]  -> uses multiple profiles
    2) profile: local  -> uses single profile (backward compatible)
    3) profile: [local, mqtthq]  -> also accepts list (flexible)
    
    Can be overridden via env var SIMCITY_MQTT_PROFILES (comma-separated).
    """
    raw = data.get("mqtt") or {}
    if not isinstance(raw, dict):
        raise ValueError("Config key 'mqtt' must be a mapping")

    # Check for env var override (comma-separated)
    env_profiles = os.getenv("SIMCITY_MQTT_PROFILES")
    if env_profiles:
        return [p.strip() for p in env_profiles.split(",") if p.strip()]

    # Check for active_profiles list
    active = raw.get("active_profiles")
    if active is not None:
        if isinstance(active, list):
            return [str(p) for p in active if p]
        else:
            raise ValueError("Config key 'mqtt.active_profiles' must be a list")

    # Check for profile (can be string or list)
    profile = raw.get("profile") or raw.get("default_profile")
    if profile is not None:
        if isinstance(profile, list):
            return [str(p) for p in profile if p]
        else:
            return [str(profile)]
    
    # Final fallback to 'local'
    return ["local"]


def _load_mqtt_configs(data: dict[str, Any], profile_names: list[str]) -> dict[str, dict[str, Any]]:
    """Load MQTT config dicts for all requested profile names.
    
    Returns a dict mapping profile_name -> mqtt_config_dict.
    If 'local' is requested but no profiles are defined, provides sensible defaults.
    """
    raw = data.get("mqtt") or {}
    if not isinstance(raw, dict):
        raise ValueError("Config key 'mqtt' must be a mapping")

    profiles = raw.get("profiles") or {}
    if not isinstance(profiles, dict):
        raise ValueError("Config key 'mqtt.profiles' must be a mapping")

    result: dict[str, dict[str, Any]] = {}
    common: dict[str, Any] = {
        k: v
        for k, v in raw.items()
        if k not in {"profiles", "profile", "active_profiles", "active_profile", "default_profile"}
    }

    for profile_name in profile_names:
        # Special case: if 'local' is requested but no profiles exist, use defaults
        if profile_name == "local" and not profiles:
            selected = {
                "host": "localhost",
                "port": 1883,
                "tls": False,
            }
        elif profile_name not in profiles:
            available = ", ".join(sorted(str(k) for k in profiles.keys()))
            raise ValueError(f"Unknown MQTT profile '{profile_name}'. Available: {available}")
        else:
            selected = profiles.get(profile_name) or {}
            if not isinstance(selected, dict):
                raise ValueError(f"Config key 'mqtt.profiles.{profile_name}' must be a mapping")

        # Merge common settings with profile-specific overrides
        result[profile_name] = {**common, **selected}

    return result


def _dict_to_mqtt_config(mqtt_dict: dict[str, Any]) -> MqttConfig:
    """Convert a MQTT config dict to an MqttConfig object."""
    host = str(mqtt_dict.get("host") or "localhost")
    port = int(mqtt_dict.get("port") or 1883)
    tls = bool(mqtt_dict.get("tls") or False)

    username_env = mqtt_dict.get("username_env")
    password_env = mqtt_dict.get("password_env")
    username = os.getenv(str(username_env)) if username_env else None
    password = os.getenv(str(password_env)) if password_env else None

    client_id_prefix = str(mqtt_dict.get("client_id_prefix") or "simcity")
    keepalive_s = int(mqtt_dict.get("keepalive_s") or 60)
    base_topic = str(mqtt_dict.get("base_topic") or "simulated-city")

    return MqttConfig(
        host=host,
        port=port,
        tls=tls,
        username=username,
        password=password,
        client_id_prefix=client_id_prefix,
        keepalive_s=keepalive_s,
        base_topic=base_topic,
    )



def _parse_simulation_config(raw: Any) -> SimulationConfig | None:
    """Parse the optional `simulation:` section from config.yaml.

    We keep this tolerant: missing or empty simulation config returns None.
    """

    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("Config key 'simulation' must be a mapping")

    timestep_minutes = int(raw.get("timestep_minutes") or 15)
    arrival_prob = float(raw.get("arrival_prob") or 0.25)
    bag_fill_delta_pct = int(raw.get("bag_fill_delta_pct") or 2)
    status_boundary_pct = int(raw.get("status_boundary_pct") or 10)

    publish_every_deposit = bool(raw.get("publish_every_deposit") or False)

    # Optional wall-clock delay between timesteps (useful for MQTT testing).
    step_delay_raw = raw.get("step_delay_s")
    if step_delay_raw is None:
        step_delay_raw = raw.get("step_delay_seconds")
    step_delay_s = float(step_delay_raw) if step_delay_raw is not None else 0.0

    start_time_raw = raw.get("start_time")
    start_time = _parse_utc_datetime(start_time_raw) if start_time_raw is not None else None

    seed_raw = raw.get("seed")
    seed = int(seed_raw) if seed_raw is not None else None

    locations_raw = raw.get("locations") or []
    if not isinstance(locations_raw, list):
        raise ValueError("Config key 'simulation.locations' must be a list")

    locations: list[SimulationLocationConfig] = []
    for item in locations_raw:
        if not isinstance(item, dict):
            raise ValueError("Each item in 'simulation.locations' must be a mapping")

        location_id = str(item.get("id") or item.get("location_id") or "").strip()
        if not location_id:
            raise ValueError("Each simulation location must have an 'id'")

        if "lat" not in item or "lon" not in item:
            raise ValueError(f"Simulation location '{location_id}' must define 'lat' and 'lon'")
        lat = float(item["lat"])
        lon = float(item["lon"])

        locations.append(SimulationLocationConfig(location_id=location_id, lat=lat, lon=lon))

    car_rerouting_phase1 = _parse_car_rerouting_phase1(raw.get("car_rerouting_phase1"))

    return SimulationConfig(
        timestep_minutes=timestep_minutes,
        arrival_prob=arrival_prob,
        bag_fill_delta_pct=bag_fill_delta_pct,
        status_boundary_pct=status_boundary_pct,
        publish_every_deposit=publish_every_deposit,
        step_delay_s=step_delay_s,
        start_time=start_time,
        seed=seed,
        locations=tuple(locations),
        car_rerouting_phase1=car_rerouting_phase1,
    )


def _parse_car_rerouting_phase1(raw: Any) -> CarReroutingPhase1Config | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("Config key 'simulation.car_rerouting_phase1' must be a mapping")

    seed = int(raw.get("seed") or 7)
    tick_seconds = float(raw.get("tick_seconds") or 1.0)
    max_ticks = int(raw.get("max_ticks") or 600)
    car_count = int(raw.get("car_count") or 20)

    blocked_raw = raw.get("blocked_segment_ids")
    if blocked_raw is None:
        blocked_raw = []
    if not isinstance(blocked_raw, list):
        raise ValueError("Config key 'simulation.car_rerouting_phase1.blocked_segment_ids' must be a list")
    blocked_segment_ids = tuple(int(item) for item in blocked_raw)

    roadwork_raw = raw.get("roadwork") or {}
    if not isinstance(roadwork_raw, dict):
        raise ValueError("Config key 'simulation.car_rerouting_phase1.roadwork' must be a mapping")

    roadwork_start_tick = int(roadwork_raw.get("start_tick") or 180)
    roadwork_end_tick = int(roadwork_raw.get("end_tick") or 300)

    roadwork_blocked_raw = roadwork_raw.get("blocked_segment_ids")
    if roadwork_blocked_raw is None:
        roadwork_blocked_raw = blocked_raw or [44105317, 733901267]
    if not isinstance(roadwork_blocked_raw, list):
        raise ValueError("Config key 'simulation.car_rerouting_phase1.roadwork.blocked_segment_ids' must be a list")

    roadwork = CarReroutingRoadworkConfig(
        start_tick=roadwork_start_tick,
        end_tick=roadwork_end_tick,
        blocked_segment_ids=tuple(int(item) for item in roadwork_blocked_raw),
    )

    routing_raw = raw.get("routing") or {}
    if not isinstance(routing_raw, dict):
        raise ValueError("Config key 'simulation.car_rerouting_phase1.routing' must be a mapping")

    routing = CarReroutingRoutingConfig(
        reroute_cooldown_ticks=int(routing_raw.get("reroute_cooldown_ticks") or 3),
        base_edge_cost=float(routing_raw.get("base_edge_cost") or 1.0),
        congestion_penalty=float(routing_raw.get("congestion_penalty") or 2.0),
        tie_breaker=str(routing_raw.get("tie_breaker") or "node_id"),
    )

    segment_pairs_raw = raw.get("segment_node_pairs") or {}
    if not isinstance(segment_pairs_raw, dict):
        raise ValueError("Config key 'simulation.car_rerouting_phase1.segment_node_pairs' must be a mapping")

    segment_node_pairs: dict[int, tuple[str, str]] = {}
    for segment_id, pair in segment_pairs_raw.items():
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("Each segment_node_pairs value must be a 2-item list [from_node, to_node]")
        segment_node_pairs[int(segment_id)] = (str(pair[0]), str(pair[1]))

    graph_raw = raw.get("graph_adjacency") or {}
    if not isinstance(graph_raw, dict):
        raise ValueError("Config key 'simulation.car_rerouting_phase1.graph_adjacency' must be a mapping")

    graph_adjacency: dict[str, tuple[str, ...]] = {}
    for node, neighbors in graph_raw.items():
        if not isinstance(neighbors, list):
            raise ValueError("Each graph_adjacency value must be a list of node ids")
        graph_adjacency[str(node)] = tuple(str(neighbor) for neighbor in neighbors)

    od_pairs_raw = raw.get("od_pairs") or []
    if not isinstance(od_pairs_raw, list):
        raise ValueError("Config key 'simulation.car_rerouting_phase1.od_pairs' must be a list")

    od_pairs: list[CarReroutingOdPair] = []
    for index, item in enumerate(od_pairs_raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Each od_pairs item must be a mapping (item {index})")
        origin = str(item.get("origin") or "").strip()
        destination = str(item.get("destination") or "").strip()
        if not origin or not destination:
            raise ValueError(f"Each od_pairs item must define origin and destination (item {index})")
        od_pairs.append(CarReroutingOdPair(origin=origin, destination=destination))

    return CarReroutingPhase1Config(
        seed=seed,
        tick_seconds=tick_seconds,
        max_ticks=max_ticks,
        car_count=car_count,
        blocked_segment_ids=blocked_segment_ids,
        roadwork=roadwork,
        routing=routing,
        segment_node_pairs=segment_node_pairs,
        graph_adjacency=graph_adjacency,
        od_pairs=tuple(od_pairs),
    )


def _load_yaml_dict(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}

    content = p.read_text(encoding="utf-8")
    loaded = yaml.safe_load(content)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file {p} must contain a YAML mapping at top level")
    return loaded


def _resolve_default_config_path(path: str | Path) -> Path:
    """Resolve a config path in a notebook-friendly way.

    When `load_config()` is called with the default relative filename
    (`config.yaml`), users often run code from a subdirectory (e.g. `notebooks/`).
    In that case we search parent directories so `config.yaml` at repo root is
    still discovered.

    If a custom path is provided (including nested relative paths), we do not
    change it.
    """

    p = Path(path)

    # Absolute paths, or already-existing relative paths, are used as-is.
    if p.is_absolute() or p.exists():
        return p

    # Only apply parent-search for bare filenames like "config.yaml".
    if p.parent != Path("."):
        return p

    def search_upwards(start: Path) -> Path | None:
        for parent in [start, *start.parents]:
            candidate = parent / p.name
            if candidate.exists():
                return candidate
        return None

    found = search_upwards(Path.cwd())
    if found is not None:
        return found

    # If cwd isn't inside the project (common in some notebook setups), also
    # search relative to this installed package location.
    found = search_upwards(Path(__file__).resolve().parent)
    if found is not None:
        return found

    return p