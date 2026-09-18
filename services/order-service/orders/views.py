from decimal import Decimal

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .catalog_client import(
    CatalogClient,
    CatalogServiceError
)

from .inventory_client import (
    InventoryClient,
    InventoryServiceError,
)

from .payment_client import (
    PaymentClient,
    PaymentServiceError,
)

from .models import Order, OrderItem
from .serializers import OrderSerializer


class OrderCreateView(APIView):

    def post(self, request):

        user_id = request.data.get("user_id")
        items = request.data.get("items")

        if not user_id:
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not items:
            return Response(
                {"detail": "items are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(items, list):
            return Response(
                {"detail": "items must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        catalog_client = CatalogClient()

        prepared_items = []
        total_price = Decimal("0.00")

        # --------------------------------
        # Step 1: Get products from Catalog
        # --------------------------------

        for item in items:

            product_id = item.get("product_id")
            quantity = item.get("quantity")

            if not product_id or not quantity:
                return Response(
                    {
                        "detail": (
                            "product_id and quantity "
                            "are required."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if quantity <= 0:
                return Response(
                    {
                        "detail": (
                            "quantity must be "
                            "greater than 0."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                product = catalog_client.get_product(
                    product_id
                )

            except CatalogServiceError as exc:
                return Response(
                    {"detail": str(exc)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not product.get("is_active"):
                return Response(
                    {
                        "detail": (
                            f"Product {product_id} "
                            "is not active."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
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

        # --------------------------------
        # Step 2: Create Order
        # --------------------------------

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
                        **item,
                    )
                    for item in prepared_items
                ]
            )

        # --------------------------------
        # Step 3: Reserve Inventory
        # --------------------------------

        inventory_client = InventoryClient()

        reserved_items = []

        try:

            for item in prepared_items:

                inventory_client.reserve(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                )

                reserved_items.append(item)

        except InventoryServiceError as exc:

            # Compensation
            for item in reserved_items:
                try:
                    inventory_client.release(
                        product_id=item["product_id"],
                        quantity=item["quantity"],
                    )
                except InventoryServiceError:
                    pass

            order.status = (
                Order.STATUS_INVENTORY_RESERVATION_FAILED
            )

            order.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return Response(
                {
                    "detail": str(exc),
                    "order_id": order.id,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # --------------------------------
        # Step 4: Create Payment
        # --------------------------------

        payment_client = PaymentClient()

        try:

            payment = payment_client.create_payment(
                order_id=order.id,
                user_id=user_id,
                amount=total_price,
            )

        except PaymentServiceError as exc:

            # Compensation
            for item in reserved_items:
                try:
                    inventory_client.release(
                        product_id=item["product_id"],
                        quantity=item["quantity"],
                    )
                except InventoryServiceError:
                    pass

            order.status = (
                Order.STATUS_PAYMENT_FAILED
            )

            order.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            return Response(
                {
                    "detail": str(exc),
                    "order_id": order.id,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # --------------------------------
        # Step 5: Update Order
        # --------------------------------

        order.status = (
            Order.STATUS_PAYMENT_PENDING
        )

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            {
                "order": OrderSerializer(
                    order
                ).data,
                "payment": payment,
            },
            status=status.HTTP_201_CREATED,
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
