import json
import os

import pika
from django.core.management.base import BaseCommand

from inventory.models import Inventory, ProcessedEvent
from inventory.events import publish_event

from django.db import transaction


EXCHANGE_NAME = "microshop.events"
QUEUE_NAME = "inventory-service"


class Command(BaseCommand):
    help = "Consume RabbitMQ events for Inventory Service"

    def handle(self, *args, **options):

        rabbitmq_url = os.getenv(
            "RABBITMQ_URL",
            "amqp://microshop:rabbitmq_password@localhost:5672/%2F",
        )

        parameters = pika.URLParameters(rabbitmq_url)

        connection = pika.BlockingConnection(parameters)
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

        channel.queue_bind(
            exchange=EXCHANGE_NAME,
            queue=QUEUE_NAME,
            routing_key="order.created",
        )

        channel.queue_bind(
            exchange=EXCHANGE_NAME,
            queue=QUEUE_NAME,
            routing_key="inventory.release_requested",
        )

        channel.basic_qos(prefetch_count=1)

        self.stdout.write(
            self.style.SUCCESS(
                "Inventory consumer started..."
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
            data = event['data']

            if event_type == "order.created":
                self.handle_order_created(event)

            elif event_type == "inventory.release_requested":
                self.handle_release_requested(data)

            channel.basic_ack(
                delivery_tag=method.delivery_tag
            )

        except Exception as exc:

            self.stderr.write(
                self.style.ERROR(
                    f"Event processing failed: {exc}"
                )
            )

            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )

    def handle_order_created(self, event):
        event_id = event["event_id"]
        data = event["data"]

        if ProcessedEvent.objects.filter(
                event_id=event_id
        ).exists():
            return

        order_id = data["order_id"]
        user_id = data["user_id"]
        items = data["items"]

        try:

            with transaction.atomic():

                for item in items:

                    inventory = (
                        Inventory.objects
                        .select_for_update()
                        .get(
                            product_id=item["product_id"]
                        )
                    )

                    available = (
                            inventory.quantity
                            - inventory.reserved_quantity
                    )

                    if available < item["quantity"]:
                        raise ValueError(
                            f"Not enough inventory for "
                            f"product {item['product_id']}"
                        )

                # Validation passed.
                # Now reserve everything.
                for item in items:
                    inventory = (
                        Inventory.objects
                        .select_for_update()
                        .get(
                            product_id=item["product_id"]
                        )
                    )

                    inventory.reserved_quantity += (
                        item["quantity"]
                    )

                    inventory.save(
                        update_fields=[
                            "reserved_quantity",
                            "updated_at",
                        ]
                    )

                ProcessedEvent.objects.create(
                    event_id=event_id
                )

            publish_event(
                "inventory.reserved",
                {
                    "order_id": order_id,
                    "user_id": user_id,
                    "items": items,
                },
            )

        except Exception as exc:

            publish_event(
                "inventory.reservation_failed",
                {
                    "order_id": order_id,
                    "user_id": user_id,
                    "items": items,
                    "reason": str(exc),
                },
            )

            raise

    def handle_release_requested(self, data):
        items = data["items"]

        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]

            inventory = Inventory.objects.get(
                product_id=product_id
            )

            if inventory.reserved_quantity < quantity:
                raise ValueError(
                    f"Cannot release inventory for product {product_id}"
                )

            inventory.reserved_quantity -= quantity

            inventory.save(
                update_fields=[
                    "reserved_quantity",
                    "updated_at",
                ]
            )