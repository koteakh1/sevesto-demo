from dataclasses import asdict
from typing import Union

import jwt as pyjwt
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from mqtt.types import BackendPayload, PayloadType, UserPayload, payload_dict_factory

USER_JWT_LIFETIME = 60 * 60 * 24  # 24 hours in seconds


def generate_user_jwt(user: User, expires: bool) -> str:
    """
    Generates a JWT for a front-end client or an IoT device.
    For front-end clients, `expires` needs to be True.
    """
    exp = int(timezone.now().timestamp() + USER_JWT_LIFETIME) if expires else None
    payload = asdict(
        UserPayload(email=user.email, exp=exp), dict_factory=payload_dict_factory
    )
    # exp must be omitted for non-expiring tokens
    if payload["exp"] is None:
        payload.pop("exp")
    token = pyjwt.encode(payload, settings.MQTT_JWT_SECRET, settings.MQTT_JWT_ALGORITHM)
    # jwt.encode actually returns a str, but has a bytes type hint, so must ignore
    return token  # type: ignore


def generate_backend_jwt() -> str:
    """
    Generates JWT for Django to publish messages to the MQTT broker.
    """
    payload = asdict(BackendPayload(), dict_factory=payload_dict_factory)
    token = pyjwt.encode(payload, settings.MQTT_JWT_SECRET, settings.MQTT_JWT_ALGORITHM)
    return token  # type: ignore


def get_jwt_payload(jwt: str) -> Union[BackendPayload, UserPayload]:
    payload = _decode_jwt(jwt)
    if payload["type"] == PayloadType.BACKEND.value:
        return BackendPayload()
    elif payload["type"] == PayloadType.USER.value:
        return UserPayload(exp=payload.get("exp"), email=payload["email"])
    raise ValueError("Invalid JWT payload type")


def _decode_jwt(jwt: str) -> dict:
    """Returns payload as a dict"""
    return pyjwt.decode(
        jwt, settings.MQTT_JWT_SECRET, algorithms=[settings.MQTT_JWT_ALGORITHM]
    )
