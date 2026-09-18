from django.http import JsonResponse

from rest_framework import generics

from .models import Inventory
from .serializers import(
    InventorySerializer,
    InventoryOperationSerializer
)

from django.db import transaction

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "service": "inventory-service",
    })


class InventoryCreateView(
    generics.CreateAPIView
):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer


class InventoryDetailView(
    generics.RetrieveAPIView
):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

    lookup_field = 'product_id'


class ReserveInventoryView(APIView):

    def post(self, request):

        serializer = InventoryOperationSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data[
            "product_id"
        ]

        quantity = serializer.validated_data[
            "quantity"
        ]

        try:

            with transaction.atomic():

                inventory = (
                    Inventory.objects
                    .select_for_update()
                    .get(
                        product_id=product_id
                    )
                )

                if (
                    inventory.available_quantity
                    < quantity
                ):
                    return Response(
                        {
                            "detail":
                                "Insufficient inventory."
                        },
                        status=status.HTTP_409_CONFLICT,
                    )

                inventory.reserved_quantity += quantity

                inventory.save(
                    update_fields=[
                        "reserved_quantity",
                        "updated_at",
                    ]
                )

            return Response(
                InventorySerializer(
                    inventory
                ).data
            )

        except Inventory.DoesNotExist:

            return Response(
                {
                    "detail":
                        "Inventory not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )


class ReleaseInventoryView(APIView):

    def post(self, request):

        serializer = InventoryOperationSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']

        try:
            with transaction.atomic():

                inventory = (
                    Inventory.objects
                    .select_for_update()
                    .get(
                        product_id=product_id
                    )
                )

                if (
                    inventory.available_quantity
                    < quantity
                ):
                    return Response(
                        {
                            "detail":
                                "Cannot release more "
                                "than reserved."
                        },
                        status=status.HTTP_409_CONFLICT,
                    )

                inventory.reserved_quantity -= quantity

                inventory.save(
                    update_fields=[
                        "reserved_quantity",
                        "updated_at",
                    ]
                )

            return Response(
                InventorySerializer(
                    inventory
                ).data
            )

        except Inventory.DoesNotExist:
            return Response(
                InventorySerializer(
                    inventory
                ).data
            )


