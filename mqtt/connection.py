import logging
from functools import lru_cache

import paho.mqtt.client as mqtt
from django.conf import settings

from mqtt.reads.jwt import generate_backend_jwt


@lru_cache(maxsize=1)
def get_mqtt_client():
    """
    lru_cache ensures that connection to the MQTT broker is only established once
    per process.
    """
    client = mqtt.Client()
    client.username_pw_set(generate_backend_jwt(), "...")
    try:
        client.connect(settings.MQTT_HOST, settings.MQTT_PORT, settings.MQTT_KEEPALIVE)
        # Starts a new thread and loops non-stop. Required to send messages
        # from the outgoing buffer, process messages from the incoming buffer
        # and handle reconnections. Every new Client instance needs its own loop.
        client.loop_start()
    except Exception as ex:
        logging.error(
            f"Failed to connect to the MQTT Broker. {ex}\n"
            "Realtime alerts may not work. Please check that you are using the latest docker-compose.yml",
            exc_info=True,
        )
    return client
