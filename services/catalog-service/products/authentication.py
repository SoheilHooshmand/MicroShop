from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings


class GatewayUser:
    def __init__(
        self,
        user_id,
        email=None,
        is_staff=False,
        is_superuser=False,
    ):
        self.id = int(user_id)
        self.pk = self.id
        self.email = email
        self.is_staff = is_staff
        self.is_superuser = is_superuser

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class GatewayAuthentication(BaseAuthentication):

    def authenticate(self, request):
        user_id = request.headers.get("X-User-ID")

        if not user_id:
            raise AuthenticationFailed(
                "Authentication required."
            )

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            raise AuthenticationFailed(
                "Invalid user ID."
            )

        user = GatewayUser(
            user_id=user_id,
            email=request.headers.get("X-User-Email"),
            is_staff=(
                request.headers.get(
                    "X-User-Staff", ""
                ).lower() == "true"
            ),
            is_superuser=(
                request.headers.get(
                    "X-User-Admin", ""
                ).lower() == "true"
            ),
        )

        return user, None


class ServiceUser:

    def __init__(self, service_name):
        self.service_name = service_name

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class ServiceAuthentication(BaseAuthentication):

    def authenticate(self, request):

        service_name = request.headers.get("X-Service-Name")
        service_token = request.headers.get("X-Service-Token")

        if not service_name or not service_token:
            raise AuthenticationFailed(
                "Service authentication required."
            )

        if service_name != "order-service":
            raise AuthenticationFailed(
                "Unknown service."
            )

        if service_token != settings.ORDER_SERVICE_TOKEN:
            raise AuthenticationFailed(
                "Invalid service token."
            )

        user = ServiceUser(service_name)

        return user, None