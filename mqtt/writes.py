import json

from main.models import Alert
from main.reads.alert import get_alert_recipients
from main.templatetags.common_tags import has_permission
from mqtt.connection import get_mqtt_client
from mqtt.reads.topic import get_alert_topic


def publish_alert_data(alert: Alert, data: dict) -> None:
    payload = json.dumps(data, default=str)
    for user in get_alert_recipients(alert):
        if has_permission(user, "main.view_alert"):
            get_mqtt_client().publish(get_alert_topic(user), payload)
