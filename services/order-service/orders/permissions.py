from rest_framework.permissions import BasePermission


class IsOrderOwner(BasePermission):
    message = "You do not have permission to access this order."

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class IsAdminUser(BasePermission):
    message = "Admin permission required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )

class IsUserAuthenticated(BasePermission):
    message = "User authenticated permission required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
        )