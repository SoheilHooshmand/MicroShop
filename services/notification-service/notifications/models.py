from django.db import models


class Notification(models.Model):

    TYPE_ORDER_CREATED = "ORDER_CREATED"
    TYPE_PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    TYPE_PAYMENT_FAILED = "PAYMENT_FAILED"
    TYPE_ORDER_CANCELLED = "ORDER_CANCELLED"

    TYPE_CHOICES = [
        (
            TYPE_ORDER_CREATED,
            "Order Created",
        ),
        (
            TYPE_PAYMENT_SUCCESS,
            "Payment Success",
        ),
        (
            TYPE_PAYMENT_FAILED,
            "Payment Failed",
        ),
        (
            TYPE_ORDER_CANCELLED,
            "Order Cancelled",
        ),
    ]

    CHANNEL_IN_APP = "IN_APP"
    CHANNEL_EMAIL = "EMAIL"
    CHANNEL_SMS = "SMS"

    CHANNEL_CHOICES = [
        (CHANNEL_IN_APP, "In App"),
        (CHANNEL_EMAIL, "Email"),
        (CHANNEL_SMS, "SMS"),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_SENT = "SENT"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
    ]

    user_id = models.BigIntegerField()

    notification_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
    )

    channel = models.CharField(
        max_length=20,
        choices=CHANNEL_CHOICES,
        default=CHANNEL_IN_APP,
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    # Reference to an entity in another service
    entity_id = models.BigIntegerField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"Notification #{self.id} "
            f"- User #{self.user_id}"
        )

class ProcessedEvent(models.Model):
    event_id = models.UUIDField(unique=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.event_id)