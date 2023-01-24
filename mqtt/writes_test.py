from unittest.mock import patch

from paho.mqtt.client import Client

from main.models import Alert
from main.test_utils import UserTestCase
from mqtt.writes import publish_alert_data


class PublishAlertDataTest(UserTestCase):
    def setUp(self):
        super().setUp()
        template = self.create_alert_template(name="test", user=self.user)
        self.alert = Alert.objects.create(
            org=template.org,
            template=template,
            visit=self.create_visit(vehicle=self.vehicle),
            vehicle=self.vehicle,
        )

    @patch.object(Client, "publish")
    @patch("mqtt.writes.has_permission")
    def test_publish_alert(self, has_permission, publish):
        has_permission.return_value = True
        publish_alert_data(self.alert, {})
        self.assertTrue(publish.called)
