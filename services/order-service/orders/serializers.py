from rest_framework import serializers

from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_id",
            "product_name",
            "unit_price",
            "quantity",
            "total_price",
        ]

        read_only_fields = [
            "id",
            "product_name",
            "unit_price",
            "total_price",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "user_id",
            "status",
            "total_price",
            "items",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "total_price",
            "items",
            "created_at",
            "updated_at",
        ]
