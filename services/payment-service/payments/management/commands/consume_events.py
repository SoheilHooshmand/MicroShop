import json
import os
import uuid

import pika
from django.core.management.base import BaseCommand

from payments.events import publish_event
from payments.models import Payment, ProcessedEvent


EXCHANGE_NAME = "microshop.events"
QUEUE_NAME = "payment-service"


class Command(BaseCommand):
    help = "Consume RabbitMQ events for Payment Service"

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

        channel.queue_bind(
            exchange=EXCHANGE_NAME,
            queue=QUEUE_NAME,
            routing_key="payment.requested",
        )

        channel.basic_qos(prefetch_count=1)

        self.stdout.write(
            self.style.SUCCESS(
                "Payment consumer started..."
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

            if event_type == "payment.requested":
                self.handle_payment_requested(event)

            channel.basic_ack(
                delivery_tag=method.delivery_tag
            )

        except Exception as exc:
            self.stderr.write(
                self.style.ERROR(
                    f"Payment processing failed: {exc}"
                )
            )

            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True,
            )

    def handle_payment_requested(self, event):

        event_id = event["event_id"]

        if ProcessedEvent.objects.filter(
                event_id=event_id
        ).exists():
            return

        data = event["data"]

        order_id = data["order_id"]

        existing_payment = Payment.objects.filter(
            order_id=order_id
        ).first()

        if existing_payment:
            ProcessedEvent.objects.create(
                event_id=event_id
            )
            return

        payment = Payment.objects.create(
            order_id=order_id,
            user_id=data["user_id"],
            amount=data["amount"],
            status="SUCCESS",
            transaction_id=str(uuid.uuid4()),
        )

        ProcessedEvent.objects.create(
            event_id=event_id
        )

        publish_event(
            "payment.succeeded",
            {
                "payment_id": payment.id,
                "order_id": payment.order_id,
                "user_id": payment.user_id,
                "amount": str(payment.amount),
                "transaction_id": payment.transaction_id,
            },
        )


