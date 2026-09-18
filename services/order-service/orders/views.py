from decimal import Decimal

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.http import JsonResponse

from .catalog_client import CatalogClient, CatalogServiceError
from .models import Order, OrderItem
from .serializers import OrderSerializer


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "service": "inventory-service",
    })

class OrderCreateView(APIView):

    def post(self, request):
        user_id = request.data.get('user_id')
        items = request.data.get('items')

        if not user_id:
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not items:
            return Response(
                {"detail": "items are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        catalog_client = CatalogClient()

        prepared_items = []
        total_price = Decimal("0.00")

        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity")

            if not product_id and not quantity:
                return Response(
                    {
                        "detail": (
                            "product_id and quantity "
                            "are required."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if quantity <= 0:
                return Response(
                    {
                        "detail": (
                            "quantity must be greater than 0."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                product = catalog_client.get_product(product_id=product_id)
            except CatalogServiceError as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not product.get("is_active"):
                return Response(
                    {
                        "detail": (
                            f"Product {product_id} "
                            "is not active."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            unit_price = Decimal(
                str(product["price"])
            )

            item_total = unit_price * quantity

            prepared_items.append(
                {
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "unit_price": unit_price,
                    "quantity": quantity,
                    "total_price": item_total,
                }
            )

            total_price += item_total

        with transaction.atomic():
            order = Order.objects.create(
                user_id=user_id,
                status=Order.STATUS_PENDING,
                total_price=total_price,
            )

            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        **items
                    )
                    for items in prepared_items
                ]
            )

            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )

class OrderDetailView(APIView):

    def get(self, request, pk):
        try:
            order = (
                Order.objects.
                prefetch_related('items')
                .get(pk=pk)
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = OrderSerializer(order)

        return Response(serializer.data)


class OrderListView(APIView):

    def get(self, request):
        orders = (
            Order.objects
            .prefetch_related("items")
            .order_by("-created_at")
        )

        serializer = OrderSerializer(
            orders,
            many=True,
        )

        return Response(serializer.data)
