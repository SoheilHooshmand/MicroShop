from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "user_id",
        "notification_type",
        "channel",
        "status",
        "created_at",
        "sent_at",
    ]

    list_filter = [
        "notification_type",
        "channel",
        "status",
    ]

    search_fields = [
        "user_id",
        "title",
        "message",
    ]