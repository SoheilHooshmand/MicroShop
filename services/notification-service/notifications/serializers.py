from rest_framework import serializers

from .models import Notification


class NotificationSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Notification

        fields = [
            "id",
            "user_id",
            "notification_type",
            "channel",
            "title",
            "message",
            "entity_id",
            "status",
            "created_at",
            "sent_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "created_at",
            "sent_at",
            "updated_at",
        ]


class NotificationCreateSerializer(
    serializers.Serializer
):

    user_id = serializers.IntegerField(
        min_value=1
    )

    notification_type = serializers.ChoiceField(
        choices=Notification.TYPE_CHOICES
    )

    channel = serializers.ChoiceField(
        choices=Notification.CHANNEL_CHOICES,
        default=Notification.CHANNEL_IN_APP,
    )

    title = serializers.CharField(
        max_length=255
    )

    message = serializers.CharField()

    entity_id = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
    )