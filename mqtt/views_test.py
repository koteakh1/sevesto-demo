import json

from django.urls import reverse
from parameterized import parameterized
from rest_framework.test import APIClient, APITestCase

from main.test_utils import ClientTestCase, create_user
from mqtt.reads.jwt import generate_backend_jwt, generate_user_jwt
from mqtt.reads.topic import get_alert_topic
from mqtt.types import AccessType


class MQTTTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()


class MQTTAuthMixinTest(MQTTTestCase):
    def test_missing_jwt(self):
        response = self.client.post(reverse("mqtt:user"))
        self.assertEqual(response.status_code, 400)

    def test_invalid_jwt(self):
        jwt = "abc"
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + jwt)
        response = self.client.post(reverse("mqtt:user"))
        self.assertEqual(response.status_code, 400)


class UserViewTest(MQTTTestCase):
    def test_backend(self):
        jwt = generate_backend_jwt()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + jwt)
        response = self.client.post(reverse("mqtt:user"))
        self.assertEqual(response.status_code, 200)

    def test_user(self):
        user, _ = create_user("user", "user@example.com", "password")
        jwt = generate_user_jwt(user, expires=False)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + jwt)
        response = self.client.post(reverse("mqtt:user"))
        self.assertEqual(response.status_code, 200)


class SuperserViewTest(MQTTTestCase):
    """
    Only the backend is considered a superuser.
    """

    def test_backend(self):
        jwt = generate_backend_jwt()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + jwt)
        response = self.client.post(reverse("mqtt:superuser"))
        self.assertEqual(response.status_code, 200)

    def test_user(self):
        user, _ = create_user("user", "user@example.com", "password")
        jwt = generate_user_jwt(user, expires=False)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + jwt)
        response = self.client.post(reverse("mqtt:superuser"))
        self.assertEqual(response.status_code, 403)


class ACLViewTest(MQTTTestCase):
    """
    Backend is granted all kinds of access, while users are limited.
    """

    def test_backend(self):
        jwt = generate_backend_jwt()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + jwt)
        response = self.client.post(reverse("mqtt:acl"))
        self.assertEqual(response.status_code, 200)

    @parameterized.expand(
        [
            (AccessType.SUBSCRIBE.value, True),
            (AccessType.READ.value, True),
            (AccessType.WRITE.value, False),
            (AccessType.READWRITE.value, False),
        ]
    )
    def test_user(self, acc, granted):
        """
        Access is granted for SUBSCRIBE & READ and denied for WRITE & READWRITE.
        """
        user, _ = create_user("user", "user@example.com", "password")
        jwt = generate_user_jwt(user, expires=False)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + jwt)

        data = {"acc": acc, "topic": get_alert_topic(user), "clientid": "test"}
        response = self.client.post(
            reverse("mqtt:acl"), data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, 200 if granted else 403)


class JWTViewTest(ClientTestCase):
    def test_get(self):
        response = self.c.get(reverse("mqtt:jwt"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("jwt", response.json())
