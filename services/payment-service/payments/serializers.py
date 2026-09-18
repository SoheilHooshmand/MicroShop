from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment

        fields = [
            "id",
            "order_id",
            "user_id",
            "amount",
            "status",
            "transaction_id",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "transaction_id",
            "created_at",
            "updated_at",
        ]


class PaymentCreateSerializer(serializers.Serializer):

    order_id = serializers.IntegerField(
        min_value=1
    )

    user_id = serializers.IntegerField(
        min_value=1
    )

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0.01,
    )