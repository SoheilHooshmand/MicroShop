import json
import os
import time
import uuid

import pika

from django.db import transaction

from .events import create_outbox_event
from .models import (
    Inventory,
    ProcessedEvent,
)


EXCHANGE_NAME = "microshop.events"

QUEUE_NAME = "inventory-service"

RETRY_QUEUE = "inventory-service.retry"

DLQ_QUEUE = "inventory-service.dlq"

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
        routing_key="order.created",
    )

    channel.queue_bind(
        queue=QUEUE_NAME,
        exchange=EXCHANGE_NAME,
        routing_key="inventory.release_requested",
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

        data = event.get(
            "data",
            {},
        )

        if event_type == "order.created":

            order_id = data["order_id"]

            for item in data["items"]:

                product_id = item[
                    "product_id"
                ]

                quantity = item[
                    "quantity"
                ]

                inventory = (
                    Inventory.objects
                    .select_for_update()
                    .get(
                        product_id=product_id
                    )
                )

                available = (
                    inventory.quantity
                    - inventory.reserved_quantity
                )

                if available < quantity:

                    create_outbox_event(
                        "inventory.reservation_failed",
                        {
                            "order_id": order_id,
                            "reason": (
                                "Not enough "
                                "inventory."
                            ),
                        },
                    )

                    return

            for item in data["items"]:

                inventory = (
                    Inventory.objects
                    .select_for_update()
                    .get(
                        product_id=item[
                            "product_id"
                        ]
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

            create_outbox_event(
                "inventory.reserved",
                {
                    "order_id": order_id,
                    "items": data["items"],
                },
            )

        elif (
            event_type
            == "inventory.release_requested"
        ):

            for item in data["items"]:

                inventory = (
                    Inventory.objects
                    .select_for_update()
                    .get(
                        product_id=item[
                            "product_id"
                        ]
                    )
                )

                quantity = item[
                    "quantity"
                ]

                inventory.reserved_quantity = max(
                    0,
                    inventory.reserved_quantity
                    - quantity,
                )

                inventory.save(
                    update_fields=[
                        "reserved_quantity",
                        "updated_at",
                    ]
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
                f"Processing failed: {exc}"
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
            f"Fatal error: {exc}"
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
                "Inventory consumer started..."
            )

            channel.start_consuming()

        except Exception as exc:

            print(
                f"Connection failed: {exc}"
            )

            time.sleep(5)