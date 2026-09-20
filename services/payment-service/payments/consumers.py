import json
import os
import time
import uuid

import pika

from django.db import transaction

from .events import create_outbox_event
from .models import (
    Payment,
    ProcessedEvent,
)


EXCHANGE_NAME = "microshop.events"

QUEUE_NAME = "payment-service"

RETRY_QUEUE = "payment-service.retry"

DLQ_QUEUE = "payment-service.dlq"

MAX_RETRIES = 3


def get_connection():

    rabbitmq_url = os.getenv(
        "RABBITMQ_URL",
        "amqp://microshop:rabbitmq_password@localhost:5672/%2F",
    )

    return pika.BlockingConnection(
        pika.URLParameters(
            rabbitmq_url
        )
    )


def setup_rabbitmq(channel):

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
        queue=QUEUE_NAME,
        exchange=EXCHANGE_NAME,
        routing_key="payment.requested",
    )

    channel.queue_declare(
        queue=RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": 10000,
            "x-dead-letter-exchange": EXCHANGE_NAME,
        },
    )

    channel.queue_declare(
        queue=DLQ_QUEUE,
        durable=True,
    )


def handle_event(event):

    event_id = uuid.UUID(
        event["event_id"]
    )

    event_type = event["event_type"]

    with transaction.atomic():

        processed = (
            ProcessedEvent.objects
            .filter(
                event_id=event_id
            )
            .first()
        )

        if processed:
            return

        ProcessedEvent.objects.create(
            event_id=event_id,
        )

        if event_type != "payment.requested":

            raise ValueError(
                f"Unknown event: {event_type}"
            )

        data = event["data"]

        order_id = data["order_id"]

        user_id = data["user_id"]

        amount = data["amount"]

        payment, created = (
            Payment.objects.get_or_create(
                order_id=order_id,
                defaults={
                    "user_id": user_id,
                    "amount": amount,
                    "status": (
                        Payment.STATUS_PENDING
                    ),
                },
            )
        )

        if not created:

            if (
                payment.status
                == Payment.STATUS_SUCCESS
            ):

                return

        payment.status = (
            Payment.STATUS_SUCCESS
        )

        payment.transaction_id = str(
            uuid.uuid4()
        )

        payment.save(
            update_fields=[
                "status",
                "transaction_id",
                "updated_at",
            ]
        )

        create_outbox_event(
            "payment.succeeded",
            {
                "order_id": order_id,
                "user_id": user_id,
                "payment_id": payment.id,
                "amount": str(
                    payment.amount
                ),
            },
        )


def publish_retry(
    channel,
    body,
):

    channel.basic_publish(
        exchange="",
        routing_key=RETRY_QUEUE,
        body=body,
        properties=pika.BasicProperties(
            delivery_mode=2
        ),
    )


def publish_dlq(
    channel,
    body,
):

    channel.basic_publish(
        exchange="",
        routing_key=DLQ_QUEUE,
        body=body,
        properties=pika.BasicProperties(
            delivery_mode=2
        ),
    )


def callback(
    channel,
    method,
    properties,
    body,
):

    try:

        event = json.loads(
            body.decode()
        )

        retry_count = event.get(
            "retry_count",
            0,
        )

        try:

            handle_event(event)

        except Exception as exc:

            print(
                f"Payment processing failed: {exc}"
            )

            if retry_count < MAX_RETRIES:

                event["retry_count"] = (
                    retry_count + 1
                )

                publish_retry(
                    channel,
                    json.dumps(event),
                )

            else:

                publish_dlq(
                    channel,
                    json.dumps(event),
                )

        channel.basic_ack(
            delivery_tag=method.delivery_tag
        )

    except Exception as exc:

        print(
            f"Fatal payment consumer error: {exc}"
        )

        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True,
        )


def consume():

    while True:

        try:

            connection = get_connection()

            channel = connection.channel()

            setup_rabbitmq(channel)

            channel.basic_qos(
                prefetch_count=1
            )

            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback,
            )

            print(
                "Payment consumer started..."
            )

            channel.start_consuming()

        except Exception as exc:

            print(
                f"Connection failed: {exc}"
            )

            time.sleep(5)