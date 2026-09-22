from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    message = "Admin permission required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsOrderService(BasePermission):

    message = "Only Order Service can access this endpoint."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.service_name == "order-service"
        )