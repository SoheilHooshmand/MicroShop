from decimal import Decimal

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .catalog_client import (
    CatalogClient,
    CatalogServiceError,
)

from .models import Order, OrderItem
from .serializers import OrderSerializer
from .events import create_outbox_event
from .permissions import IsOrderOwner, IsUserAuthenticated


class ReadAuthWriteAdminMixin:
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsOrderOwner()]
        return [IsUserAuthenticated()]

class OrderCreateView(ReadAuthWriteAdminMixin, APIView):

    def post(self, request):
        user_id = request.user.id

        if not user_id:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        items = request.data.get("items", [])

        if not items:
            return Response(
                {"detail": "At least one item is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        catalog_client = CatalogClient()
        order_items = []
        total_price = 0

        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]

            product = catalog_client.get_product(product_id)

            if not product.get("is_active", False):
                return Response(
                    {"detail": f"Product {product_id} is not active."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            unit_price = product["price"]
            product_name = product["name"]
            item_total = float(unit_price) * quantity
            total_price += item_total

            order_items.append({
                "product_id": product_id,
                "product_name": product_name,
                "unit_price": unit_price,
                "quantity": quantity,
                "total_price": item_total,
            })

        with transaction.atomic():
            order = Order.objects.create(
                user_id=user_id,
                status="PENDING",
                total_price=total_price,
            )

            for item in order_items:
                OrderItem.objects.create(
                    order=order,
                    product_id=item["product_id"],
                    product_name=item["product_name"],
                    unit_price=item["unit_price"],
                    quantity=item["quantity"],
                    total_price=item["total_price"],
                )

            create_outbox_event(
                "order.created",
                {
                    "order_id": order.id,
                    "user_id": order.user_id,
                    "total_price": str(order.total_price),
                    "items": [
                        {
                            "product_id": item["product_id"],
                            "quantity": item["quantity"],
                        }
                        for item in order_items
                    ],
                },
            )

        return Response(
            {
                "order_id": order.id,
                "status": order.status,
                "total_price": str(order.total_price),
                "message": "Order created and processing started.",
            },
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(ReadAuthWriteAdminMixin, APIView):

    def get(self, request, pk):
        try:
            order = (
                Order.objects
                .prefetch_related("items")
                .get(pk=pk)
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        self.check_object_permissions(request, order)

        serializer = OrderSerializer(order)
        return Response(serializer.data)


class OrderListView(ReadAuthWriteAdminMixin, APIView):

    def get(self, request):
        user_id = request.user.id

        if not user_id:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        orders = (
            Order.objects
            .filter(user_id=user_id)
            .prefetch_related("items")
            .order_by("-created_at")
        )

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)