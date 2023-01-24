from django.contrib.auth.models import User

from mqtt.types import AccessRequest, AccessType, UserPayload

ALERT_TOPIC_ROOT = "alerts"


def get_alert_topic(user: User) -> str:
    return f"{ALERT_TOPIC_ROOT}/{user.email}"


def get_email_from_alert_topic(topic: str) -> str:
    return topic.split("/")[1]


def is_alert_topic(topic: str) -> bool:
    return topic.startswith(ALERT_TOPIC_ROOT)


def grant_topic_access(payload: UserPayload, access_request: AccessRequest) -> bool:
    if is_alert_topic(access_request.topic):
        valid_access = access_request.acc in {AccessType.SUBSCRIBE, AccessType.READ}
        valid_email = payload.email == get_email_from_alert_topic(access_request.topic)
        return valid_access and valid_email
    return False
