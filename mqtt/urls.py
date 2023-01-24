from django.urls import path

from . import views

app_name = "mqtt"

# If user, superuser or acl paths are changed, the corresponding
# paths in mosquitto.conf must be changed as well.
urlpatterns = [
    path("user", views.UserView.as_view(), name="user"),
    path("superuser", views.SuperuserView.as_view(), name="superuser"),
    path("acl", views.ACLView.as_view(), name="acl"),
    path("jwt", views.JWTView.as_view(), name="jwt"),
]
