import json
import os

import pika
from django.core.management.base import BaseCommand

from orders.events import publish_event
from orders.models import Order, ProcessedEvent


EXCHANGE_NAME = "microshop.events"
QUEUE_NAME = "order-service"


class Command(BaseCommand):
    help = "Consume RabbitMQ events for Order Service"

    def handle(self, *args, **options):

        rabbitmq_url = os.getenv(
            "RABBITMQ_URL",
            "amqp://microshop:rabbitmq_password@localhost:5672/%2F",
        )

        connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )

        channel = connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type="topic",
            durable=True,
        )

        channel.queue_declare(
            queue=QUEUE_NAME,
            durable=True,
        )

        routing_keys = [
            "inventory.reserved",
            "inventory.reservation_failed",
            "payment.succeeded",
            "payment.failed",
        ]

        for routing_key in routing_keys:
            channel.queue_bind(
                exchange=EXCHANGE_NAME,
                queue=QUEUE_NAME,
                routing_key=routing_key,
            )

        channel.basic_qos(prefetch_count=1)

        self.stdout.write(
            self.style.SUCCESS(
                "Order consumer started..."
            )
        )

        channel.basic_consume(
            queue=QUEUE_NAME,
            on_message_callback=self.process_message,
            auto_ack=False,
        )

        channel.start_consuming()

    def process_message(
        self,
        channel,
        method,
        properties,
        body,
    ):
        try:
            event = json.loads(body)

            event_type = event["event_type"]
            data = event["data"]
            event_id = event["event_id"]

            if ProcessedEvent.objects.filter(
                    event_id=event_id
            ).exists():
                return

            if event_type == "inventory.reserved":
                self.handle_inventory_reserved(data)

            elif event_type == "inventory.reservation_failed":
                self.handle_inventory_failed(data)

            elif event_type == "payment.succeeded":
                self.handle_payment_succeeded(data)

            elif event_type == "payment.failed":
                self.handle_payment_failed(data)

            ProcessedEvent.objects.create(
                event_id=event_id
            )

            channel.basic_ack(
                delivery_tag=method.delivery_tag
            )

        except Exception as exc:
            self.stderr.write(
                self.style.ERROR(
                    f"Order event failed: {exc}"
                )
            )

            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True,
            )

    def handle_inventory_reserved(self, data):

        order = Order.objects.get(
            id=data["order_id"]
        )

        if order.status != "PENDING":
            return

        order.status = "INVENTORY_RESERVED"

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        publish_event(
            "payment.requested",
            {
                "order_id": order.id,
                "user_id": order.user_id,
                "amount": str(order.total_price),
            },
        )

    def handle_inventory_failed(self, data):

        order = Order.objects.get(
            id=data["order_id"]
        )

        if order.status != "PENDING":
            return

        order.status = "INVENTORY_RESERVATION_FAILED"

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )


    def handle_payment_succeeded(self, data):

        order = Order.objects.get(
            id=data["order_id"]
        )

        order.status = "PAID"

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    def handle_payment_failed(self, data):

        order = Order.objects.get(
            id=data["order_id"]
        )

        order.status = "PAYMENT_FAILED"

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        publish_event(
            "inventory.release_requested",
            {
                "order_id": order.id,
                "items": list(
                    order.items.values(
                        "product_id",
                        "quantity",
                    )
                ),
            },
        )