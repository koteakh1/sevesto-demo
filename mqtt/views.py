import json
from typing import Optional, Union

import jwt as pyjwt
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from mqtt.reads.jwt import generate_user_jwt, get_jwt_payload
from mqtt.reads.topic import grant_topic_access
from mqtt.types import AccessRequest, AccessType, BackendPayload, UserPayload

User = get_user_model()


class MQTTAuthMixin:
    """
    Ensures that a valid JWT is present in the request headers
    and sets its decoded payload as an attribute.
    """

    payload: Union[BackendPayload, UserPayload]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        jwt = self._get_jwt(self.request.headers)
        if jwt is None:
            return HttpResponseBadRequest()

        try:
            self.payload = get_jwt_payload(jwt)
        except pyjwt.PyJWTError:
            # Token has been tampered with (expiry is handled by mosquitto-go-auth)
            return HttpResponseBadRequest()

        return super().dispatch(*args, **kwargs)

    def _get_jwt(self, headers: dict) -> Optional[str]:
        """
        Authorization format: `Bearer <jwt>`
        """
        try:
            return headers["Authorization"].split(" ")[1]
        except (KeyError, IndexError):
            return None


class UserView(MQTTAuthMixin, View):
    """
    Check if JWT's owner exists.
    """

    def post(self, request):
        if isinstance(self.payload, BackendPayload):
            return HttpResponse()
        elif isinstance(self.payload, UserPayload):
            # Maybe user was deleted after the token was generated
            if User.objects.filter(email=self.payload.email).exists():
                return HttpResponse()
        return HttpResponseForbidden()


class SuperuserView(MQTTAuthMixin, View):
    """
    Check if JWT's owner is a superuser (i.e. granted full access).
    Only the backend is considered a superuser.
    """

    def post(self, request):
        if isinstance(self.payload, BackendPayload):
            return HttpResponse()
        return HttpResponseForbidden()


class ACLView(MQTTAuthMixin, View):
    """
    Check if JWT's owner is granted partial access.

    mosquitto-go-auth will only call this endpoint if the user is not
    a superuser.
    """

    def post(self, request):
        if isinstance(self.payload, BackendPayload):
            # Although this should not happen, because the backend
            # is a superuser we're still checking for it just to be safe.
            return HttpResponse()
        elif isinstance(self.payload, UserPayload):
            if grant_topic_access(self.payload, self._get_access_request()):
                return HttpResponse()
        return HttpResponseForbidden()

    def _get_access_request(self) -> AccessRequest:
        data = json.loads(self.request.body.decode("utf-8"))
        return AccessRequest(
            acc=AccessType(data["acc"]), clientid=data["clientid"], topic=data["topic"]
        )


class JWTView(LoginRequiredMixin, View):
    def get(self, request):
        return JsonResponse({"jwt": generate_user_jwt(request.user, True)})
