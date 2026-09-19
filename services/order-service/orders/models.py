from django.db import models
from django.utils import timezone

import uuid

class Order(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_INVENTORY_RESERVED = "INVENTORY_RESERVED"
    STATUS_PAYMENT_PENDING = "PAYMENT_PENDING"
    STATUS_PAID = "PAID"
    STATUS_PROCESSING = "PROCESSING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_PAYMENT_FAILED = "PAYMENT_FAILED"
    STATUS_INVENTORY_RESERVATION_FAILED = "INVENTORY_RESERVATION_FAILED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_INVENTORY_RESERVED, "Inventory Reserved"),
        (STATUS_PAYMENT_PENDING, "Payment Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (
            STATUS_PAYMENT_FAILED,
            "Payment Failed",
        ),
        (
            STATUS_INVENTORY_RESERVATION_FAILED,
            "Inventory Reservation Failed",
        ),
    ]

    user_id = models.BigIntegerField()

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product_id = models.BigIntegerField()

    #Snapshot
    product_name = models.CharField(max_length=200)

    #Snapshot
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    quantity = models.PositiveIntegerField()

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    def __str__(self):
        return (
            f"Order #{self.order_id} - "
            f"Product #{self.product_id}"
        )


class ProcessedEvent(models.Model):
    event_id = models.UUIDField(unique=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.event_id)

class OutboxEvent(models.Model):

    event_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    event_type = models.CharField(
        max_length=100,
    )

    payload = models.JSONField()

    published = models.BooleanField(
        default=False,
    )

    attempts = models.PositiveIntegerField(
        default=0,
    )

    available_at = models.DateTimeField(
        default=timezone.now,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_error = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"{self.event_type} - "
            f"{self.event_id}"
        )
