from __future__ import annotations

import json
import logging
import socket
import ssl
from typing import TYPE_CHECKING
import threading
import time

import certifi

from .config import MqttConfig

if TYPE_CHECKING:
    import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MqttConnector:
    """MQTT client with automatic reconnection."""

    def __init__(self, cfg: MqttConfig, *, client_id_suffix: str | None = None):
        try:
            import paho.mqtt.client as mqtt
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "paho-mqtt is required to use simulated_city.mqtt. "
                "Install dependencies (e.g. `pip install -e .`) and try again."
            ) from e

        self.cfg = cfg
        self._client_id = _make_client_id(cfg.client_id_prefix, client_id_suffix)
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self._client_id)
        self.connected = threading.Event()

        if cfg.username is not None:
            self.client.username_pw_set(cfg.username, password=cfg.password)

        if cfg.tls:
            context = ssl.create_default_context(cafile=certifi.where())
            self.client.tls_set_context(context)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.cfg.host}:{self.cfg.port}")
            self.connected.set()
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    def _on_disconnect(self, client, userdata, flags, reason, properties):
        reason_text = str(reason)
        reason_code = getattr(reason, "value", None)
        is_normal = reason_code == 0 or reason_text == "Normal disconnection"
        if is_normal:
            logger.info(f"Disconnected from MQTT broker (reason={reason}).")
        else:
            logger.warning(f"Disconnected from MQTT broker (reason={reason}). Reconnecting...")
        self.connected.clear()

    def connect(self):
        """Connect the client and start the network loop."""
        try:
            self.client.connect(self.cfg.host, self.cfg.port, keepalive=self.cfg.keepalive_s)
            self.client.loop_start()
        except (OSError, socket.gaierror, ssl.SSLError) as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            raise

    def disconnect(self):
        """Disconnect the client and stop the network loop."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker.")

    def wait_for_connection(self, timeout: float = 10.0) -> bool:
        """Wait for the client to connect."""
        return self.connected.wait(timeout)


class MqttPublisher:
    """A simple MQTT publisher."""

    def __init__(self, connector: MqttConnector):
        self.client = connector.client

    def publish_json(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        """Publish a JSON string to a topic."""
        if not self.client.is_connected():
             logger.warning("MQTT client not connected. Message may not be published.")
        result = self.client.publish(topic, payload=payload, qos=qos, retain=retain)
        # For QoS > 0, this will block until the message is sent.
        # For QoS = 0, it returns immediately.
        if qos > 0:
            result.wait_for_publish()
        return result


def _make_client_id(prefix: str, suffix: str | None) -> str:
    """Create a client ID from a prefix and an optional suffix."""
    safe_prefix = prefix.strip() or "simcity"
    if suffix:
        return f"{safe_prefix}-{suffix}"
    return safe_prefix


def connect_mqtt(cfg: MqttConfig, *, client_id_suffix: str | None = None, timeout_s: float = 10.0):
    """Connect to MQTT and return the connected paho client.

    The returned client stores the underlying connector on
    `client._simulated_city_connector` so notebooks can disconnect cleanly.
    """

    max_attempts = 3
    connector = MqttConnector(cfg, client_id_suffix=client_id_suffix)
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            connector.connect()
            if connector.wait_for_connection(timeout=timeout_s):
                break
            raise TimeoutError(f"Could not connect to MQTT broker at {cfg.host}:{cfg.port}")
        except Exception as exc:
            last_error = exc
            if hasattr(connector, "disconnect"):
                try:
                    connector.disconnect()
                except Exception:
                    pass
            if attempt < max_attempts:
                time.sleep(0.25 * attempt)
                connector = MqttConnector(cfg, client_id_suffix=client_id_suffix)
                continue
            raise last_error

    client = connector.client
    setattr(client, "_simulated_city_connector", connector)
    return client


def publish_json_checked(
    client,
    topic: str,
    data: dict,
    *,
    qos: int = 1,
    retain: bool = False,
    timeout_s: float = 3.0,
) -> bool:
    """Publish JSON and verify delivery by subscribing and observing the payload."""

    payload = json.dumps(data, separators=(",", ":"), sort_keys=True)
    observed = threading.Event()

    def _matches_payload(message_payload: bytes) -> bool:
        return message_payload.decode("utf-8") == payload

    callback_name = f"_simcity_verify_{int(time.time() * 1_000_000)}"

    def _on_topic_message(_client, _userdata, msg):
        if _matches_payload(msg.payload):
            observed.set()

    supports_callbacks = all(
        hasattr(client, attr)
        for attr in ("message_callback_add", "message_callback_remove", "subscribe", "unsubscribe")
    )

    if supports_callbacks:
        client.message_callback_add(topic, _on_topic_message)
        client.subscribe(topic, qos=qos)

    publish_result = client.publish(topic, payload=payload, qos=qos, retain=retain)
    if hasattr(publish_result, "wait_for_publish"):
        publish_result.wait_for_publish()

    if supports_callbacks:
        is_verified = observed.wait(timeout=timeout_s)
        client.message_callback_remove(topic)
        client.unsubscribe(topic)
        if not is_verified:
            raise RuntimeError(f"Publish verification timed out for topic '{topic}'")
        return True

    result_code = getattr(publish_result, "rc", 0)
    if result_code != 0:
        raise RuntimeError(f"Publish failed for topic '{topic}' with rc={result_code}")
    return True
