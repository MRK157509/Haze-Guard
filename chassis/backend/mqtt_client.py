import json
import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger("mqtt_client")

MQTT_BROKER_HOST = "localhost"   # will become Mandar's reachable path via Tailscale later — see note below
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "hazeguard/classifications"   # confirm this exact topic name with Mandar

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        logger.info(f"Connected to MQTT broker, subscribing to {MQTT_TOPIC}")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error(f"Failed to connect to MQTT broker: {reason_code}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        logger.info(f"Received message on {msg.topic}: {payload}")
        # TODO: hand off to a processing function once DB models exist
        # process_classification(payload)
    except json.JSONDecodeError:
        logger.error(f"Received non-JSON payload on {msg.topic}: {msg.payload}")

def create_mqtt_client():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
    return client