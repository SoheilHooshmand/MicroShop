from django.db import models

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