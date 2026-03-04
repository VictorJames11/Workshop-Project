from textwrap import dedent

from simulated_city.config import load_config


def test_load_config_defaults_when_missing(tmp_path) -> None:
    """Test that default config loads when file is missing."""
    cfg = load_config(tmp_path / "missing.yaml")
    assert cfg.mqtt.host
    assert cfg.mqtt.port
    # Should have at least the default 'local' profile
    assert "local" in cfg.mqtt_configs or len(cfg.mqtt_configs) > 0


def test_load_config_reads_yaml(tmp_path) -> None:
    """Test reading YAML config with multi-broker structure."""
    p = tmp_path / "config.yaml"
    p.write_text(
        """
        mqtt:
          active_profiles: [default]
          profiles:
            default:
              host: example.com
              port: 1883
              tls: false
          client_id_prefix: demo
          keepalive_s: 30
        """.strip(),
        encoding="utf-8",
    )

    cfg = load_config(p)
    assert cfg.mqtt.host == "example.com"
    assert cfg.mqtt.port == 1883
    assert cfg.mqtt.tls is False
    assert cfg.mqtt.client_id_prefix == "demo"
    assert cfg.mqtt.keepalive_s == 30


def test_load_config_finds_parent_config_yaml(tmp_path, monkeypatch) -> None:
    """Test that config is found in parent directories."""
    # Simulate running from a subdirectory (like notebooks/)
    root = tmp_path
    (root / "config.yaml").write_text(
        """
        mqtt:
          active_profiles: [parent]
          profiles:
            parent:
              host: parent.example.com
              port: 1883
              tls: false
          client_id_prefix: demo
          keepalive_s: 30
        """.strip(),
        encoding="utf-8",
    )

    subdir = root / "notebooks"
    subdir.mkdir()
    monkeypatch.chdir(subdir)

    cfg = load_config("config.yaml")
    assert cfg.mqtt.host == "parent.example.com"

def test_load_config_multi_broker_with_active_profiles(tmp_path) -> None:
    """Test multi-broker configuration with active_profiles list."""
    p = tmp_path / "config.yaml"
    p.write_text(
        """
        mqtt:
          active_profiles: [local, public]
          profiles:
            local:
              host: localhost
              port: 1883
              tls: false
            public:
              host: broker.example.com
              port: 1883
              tls: false
          client_id_prefix: multi-test
          keepalive_s: 60
          base_topic: test-city
        """.strip(),
        encoding="utf-8",
    )

    cfg = load_config(p)
    
    # Primary broker (first in list)
    assert cfg.mqtt.host == "localhost"
    assert cfg.mqtt.port == 1883
    
    # All brokers available by name
    assert "local" in cfg.mqtt_configs
    assert "public" in cfg.mqtt_configs
    assert cfg.mqtt_configs["local"].host == "localhost"
    assert cfg.mqtt_configs["public"].host == "broker.example.com"


def test_load_config_single_broker_with_active_profiles(tmp_path) -> None:
    """Test single-broker configuration using active_profiles."""
    p = tmp_path / "config.yaml"
    p.write_text(
        """
        mqtt:
          active_profiles: [local]
          profiles:
            local:
              host: localhost
              port: 1883
              tls: false
          client_id_prefix: single-test
          keepalive_s: 60
          base_topic: test-city
        """.strip(),
        encoding="utf-8",
    )

    cfg = load_config(p)
    
    # Primary broker
    assert cfg.mqtt.host == "localhost"
    
    # Only local broker in configs
    assert "local" in cfg.mqtt_configs
    assert len(cfg.mqtt_configs) == 1


def test_load_config_parses_phase2_car_rerouting_settings(tmp_path) -> None:
    """Test explicit Phase 2 config fields for tick/roadwork/routing."""
    p = tmp_path / "config.yaml"
    p.write_text(
        dedent(
            """
        mqtt:
          active_profiles: [local]
          profiles:
            local:
              host: localhost
              port: 1883
              tls: false
        simulation:
          car_rerouting_phase1:
            seed: 11
            tick_seconds: 0.5
            max_ticks: 700
            car_count: 30
            blocked_segment_ids: [44105317]
            roadwork:
              start_tick: 180
              end_tick: 300
              blocked_segment_ids: [44105317, 733901267]
            routing:
              reroute_cooldown_ticks: 4
              base_edge_cost: 1.25
              congestion_penalty: 2.5
              tie_breaker: hops
            segment_node_pairs:
              "44105317": [N2, N3]
              "733901267": [N4, N5]
            graph_adjacency:
              N1: [N2]
              N2: [N1, N3]
              N3: [N2]
            od_pairs:
              - origin: N1
                destination: N3
            """
        ).strip(),
        encoding="utf-8",
    )

    cfg = load_config(p)
    assert cfg.simulation is not None
    phase1 = cfg.simulation.car_rerouting_phase1
    assert phase1 is not None

    assert phase1.seed == 11
    assert phase1.tick_seconds == 0.5
    assert phase1.max_ticks == 700
    assert phase1.car_count == 30
    assert phase1.roadwork.start_tick == 180
    assert phase1.roadwork.end_tick == 300
    assert phase1.roadwork.blocked_segment_ids == (44105317, 733901267)
    assert phase1.routing.reroute_cooldown_ticks == 4
    assert phase1.routing.base_edge_cost == 1.25
    assert phase1.routing.congestion_penalty == 2.5
    assert phase1.routing.tie_breaker == "hops"


def test_load_config_phase2_defaults_for_roadwork_and_routing(tmp_path) -> None:
    """Test Phase 2 defaults are applied when roadwork/routing are omitted."""
    p = tmp_path / "config.yaml"
    p.write_text(
        dedent(
            """
        mqtt:
          active_profiles: [local]
          profiles:
            local:
              host: localhost
              port: 1883
              tls: false
        simulation:
          car_rerouting_phase1:
            segment_node_pairs:
              "44105317": [N2, N3]
            graph_adjacency:
              N1: [N2]
              N2: [N1]
            od_pairs:
              - origin: N1
                destination: N2
            """
        ).strip(),
        encoding="utf-8",
    )

    cfg = load_config(p)
    assert cfg.simulation is not None
    phase1 = cfg.simulation.car_rerouting_phase1
    assert phase1 is not None

    assert phase1.tick_seconds == 1.0
    assert phase1.max_ticks == 600
    assert phase1.roadwork.start_tick == 180
    assert phase1.roadwork.end_tick == 300
    assert phase1.roadwork.blocked_segment_ids == (44105317, 733901267)
    assert phase1.routing.reroute_cooldown_ticks == 3
    assert phase1.routing.base_edge_cost == 1.0
    assert phase1.routing.congestion_penalty == 2.0
    assert phase1.routing.tie_breaker == "node_id"