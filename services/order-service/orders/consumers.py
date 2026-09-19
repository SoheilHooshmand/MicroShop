import json
import os
import time
import uuid

import pika

from django.db import transaction

from orders.events import create_outbox_event
from orders.models import (
    Order,
    ProcessedEvent,
)


EXCHANGE_NAME = "microshop.events"

QUEUE_NAME = "order-service"

RETRY_QUEUE = "order-service.retry"

DLQ_QUEUE = "order-service.dlq"

MAX_RETRIES = 3


def get_connection():

    rabbitmq_url = os.getenv(
        "RABBITMQ_URL",
        "amqp://microshop:rabbitmq_password@localhost:5672/%2F",
    )

    return pika.BlockingConnection(
        pika.URLParameters(rabbitmq_url)
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
        routing_key="inventory.reserved",
    )

    channel.queue_bind(
        queue=QUEUE_NAME,
        exchange=EXCHANGE_NAME,
        routing_key="inventory.reservation_failed",
    )

    channel.queue_bind(
        queue=QUEUE_NAME,
        exchange=EXCHANGE_NAME,
        routing_key="payment.succeeded",
    )

    channel.queue_bind(
        queue=QUEUE_NAME,
        exchange=EXCHANGE_NAME,
        routing_key="payment.failed",
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


def is_event_processed(event_id):

    return ProcessedEvent.objects.filter(
        event_id=event_id
    ).exists()


def mark_event_processed(
    event_id,
    event_type,
):

    ProcessedEvent.objects.create(
        event_id=event_id,
        event_type=event_type,
    )


def handle_event(event):

    event_id = uuid.UUID(
        event["event_id"]
    )

    event_type = event["event_type"]

    if is_event_processed(event_id):
        print(
            f"Event {event_id} already processed."
        )
        return

    with transaction.atomic():

        processed = ProcessedEvent.objects.filter(
            event_id=event_id
        ).first()

        if processed:
            return

        ProcessedEvent.objects.create(
            event_id=event_id,
            event_type=event_type,
        )

        data = event.get(
            "data",
            {},
        )

        if event_type == "inventory.reserved":

            order_id = data["order_id"]

            order = Order.objects.get(
                id=order_id
            )

            if order.status == "PENDING":

                order.status = (
                    "INVENTORY_RESERVED"
                )

                order.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

                create_outbox_event(
                    "payment.requested",
                    {
                        "order_id": order.id,
                        "user_id": order.user_id,
                        "amount": str(
                            order.total_price
                        ),
                    },
                )

        elif event_type == "inventory.reservation_failed":

            order_id = data["order_id"]

            order = Order.objects.get(
                id=order_id
            )

            order.status = (
                "INVENTORY_RESERVATION_FAILED"
            )

            order.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        elif event_type == "payment.succeeded":

            order_id = data["order_id"]

            order = Order.objects.get(
                id=order_id
            )

            order.status = "PAID"

            order.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

        elif event_type == "payment.failed":

            order_id = data["order_id"]

            order = Order.objects.get(
                id=order_id
            )

            order.status = "PAYMENT_FAILED"

            order.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            create_outbox_event(
                "inventory.release_requested",
                {
                    "order_id": order.id,
                    "items": [
                        {
                            "product_id": item.product_id,
                            "quantity": item.quantity,
                        }
                        for item in order.items.all()
                    ],
                },
            )

        else:

            raise ValueError(
                f"Unknown event: {event_type}"
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
            delivery_mode=2,
            content_type="application/json",
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
            delivery_mode=2,
            content_type="application/json",
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
            body.decode("utf-8")
        )

        retry_count = event.get(
            "retry_count",
            0,
        )

        try:

            handle_event(event)

        except Exception as exc:

            print(
                f"Event processing failed: {exc}"
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
            f"Fatal consumer error: {exc}"
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
                "Order consumer started..."
            )

            channel.start_consuming()

        except Exception as exc:

            print(
                f"Consumer connection failed: {exc}"
            )

            time.sleep(5)