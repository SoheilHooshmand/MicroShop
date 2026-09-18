from django.urls import path

from .views import (
    NotificationCreateView,
    NotificationDetailView,
    NotificationListView,
    NotificationMarkAsSentView,
)


urlpatterns = [

    path(
        "",
        NotificationListView.as_view(),
        name="notification-list",
    ),

    path(
        "create/",
        NotificationCreateView.as_view(),
        name="notification-create",
    ),

    path(
        "<int:pk>/",
        NotificationDetailView.as_view(),
        name="notification-detail",
    ),

    path(
        "<int:pk>/mark-sent/",
        NotificationMarkAsSentView.as_view(),
        name="notification-mark-sent",
    ),
]