from django.db import models
from django.utils import timezone

import uuid

class Inventory(models.Model):
    product_id = models.BigIntegerField(
        unique=True,
    )

    quantity = models.PositiveIntegerField(
        default=0,
    )

    reserved_quantity = models.PositiveIntegerField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity

    def __str__(self):
        return (
            f"Product {self.product_id} "
            f"({self.available_quantity} available)"
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
        max_length=100
    )

    payload = models.JSONField()

    published = models.BooleanField(
        default=False
    )

    attempts = models.PositiveIntegerField(
        default=0
    )

    available_at = models.DateTimeField(
        default=timezone.now
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True
    )

    last_error = models.TextField(
        blank=True
    )

    class Meta:
        ordering = ["created_at"]