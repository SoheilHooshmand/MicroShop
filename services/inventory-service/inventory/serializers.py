from rest_framework import serializers

from .models import Inventory

class InventorySerializer(serializers.ModelSerializer):

    available_quantity = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = Inventory
        fields = [
            "id",
            "product_id",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "available_quantity",
            "created_at",
            "updated_at",
        ]


class InventoryOperationSerializer(
    serializers.Serializer
):

    product_id = serializers.IntegerField()

    quantity = serializers.IntegerField(
        min_value=1
    )