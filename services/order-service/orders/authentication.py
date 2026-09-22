from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


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

        email = request.headers.get("X-User-Email")

        is_staff = (
            request.headers.get("X-User-Staff", "").lower()
            == "true"
        )

        is_superuser = (
            request.headers.get("X-User-Admin", "").lower()
            == "true"
        )

        user = GatewayUser(
            user_id=user_id,
            email=email,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

        return user, None