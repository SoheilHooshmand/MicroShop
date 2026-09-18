import json
import os

import pika
from django.core.management.base import BaseCommand

from notifications.models import Notification, ProcessedEvent


EXCHANGE_NAME = "microshop.events"
QUEUE_NAME = "notification-service"


class Command(BaseCommand):
    help = "Consume RabbitMQ events for Notification Service"

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
            "order.created",
            "payment.succeeded",
            "payment.failed",
            "order.cancelled",
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
                "Notification consumer started..."
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

            if event_type == "order.created":
                self.create_notification(
                    user_id=data["user_id"],
                    notification_type="ORDER_CREATED",
                    title="Order Created",
                    message=f"Order #{data['order_id']} was created.",
                    entity_id=data["order_id"],
                )

            elif event_type == "payment.succeeded":
                self.create_notification(
                    user_id=data["user_id"],
                    notification_type="PAYMENT_SUCCESS",
                    title="Payment Successful",
                    message=f"Payment for order #{data['order_id']} was successful.",
                    entity_id=data["order_id"],
                )

            elif event_type == "payment.failed":
                self.create_notification(
                    user_id=data["user_id"],
                    notification_type="PAYMENT_FAILED",
                    title="Payment Failed",
                    message=f"Payment for order #{data['order_id']} failed.",
                    entity_id=data["order_id"],
                )

            elif event_type == "order.cancelled":
                self.create_notification(
                    user_id=data["user_id"],
                    notification_type="ORDER_CANCELLED",
                    title="Order Cancelled",
                    message=f"Order #{data['order_id']} was cancelled.",
                    entity_id=data["order_id"],
                )

            ProcessedEvent.objects.create(
                event_id=event_id
            )

            channel.basic_ack(
                delivery_tag=method.delivery_tag
            )

        except Exception as exc:
            self.stderr.write(
                self.style.ERROR(
                    f"Notification processing failed: {exc}"
                )
            )

            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True,
            )

    def create_notification(
        self,
        user_id,
        notification_type,
        title,
        message,
        entity_id,
    ):
        Notification.objects.create(
            user_id=user_id,
            notification_type=notification_type,
            channel="IN_APP",
            title=title,
            message=message,
            entity_id=entity_id,
        )