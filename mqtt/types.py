from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional, Tuple

from django.contrib.auth import get_user_model

User = get_user_model()


class PayloadType(Enum):
    """
    Backend refers to the Django app that's publishing data to the MQTT broker.
    User refers to a front-end client or an IoT device.
    """

    BACKEND = "backend"
    USER = "user"


@dataclass
class BackendPayload:
    type: PayloadType = PayloadType.BACKEND


@dataclass
class UserPayload:
    email: str
    exp: Optional[int]
    type: PayloadType = PayloadType.USER


def payload_dict_factory(payload: List[Tuple[str, Any]]) -> dict:
    """
    Converts enum members to their values.

    payload is a list of tuples, where each tuple is a
    field name - field value pair.
    """
    return {k: v.value if isinstance(v, Enum) else v for k, v in payload}


class AccessType(Enum):
    """
    Enumerates topic access types according to mosquitto-go-auth's spec:
    https://github.com/iegomez/mosquitto-go-auth#jwt
    """

    READ = 1
    WRITE = 2
    READWRITE = 3
    SUBSCRIBE = 4


@dataclass
class AccessRequest:
    """
    Represents a request received by mosquitto-go-auth to check
    access to a topic. https://github.com/iegomez/mosquitto-go-auth#jwt
    """

    acc: AccessType
    clientid: str
    topic: str
