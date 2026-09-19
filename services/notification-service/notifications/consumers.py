import json
import os
import time
import uuid

import pika

from django.db import transaction

from .models import (
    Notification,
    ProcessedEvent,
)


EXCHANGE_NAME = "microshop.events"

QUEUE_NAME = "notification-service"

RETRY_QUEUE = "notification-service.retry"

DLQ_QUEUE = "notification-service.dlq"

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

    for routing_key in [
        "order.created",
        "payment.succeeded",
        "payment.failed",
        "order.cancelled",
    ]:

        channel.queue_bind(
            queue=QUEUE_NAME,
            exchange=EXCHANGE_NAME,
            routing_key=routing_key,
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

    event_type = event[
        "event_type"
    ]

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

        data = event.get(
            "data",
            {},
        )

        if event_type == "order.created":

            user_id = data["user_id"]

            title = "Order Created"

            message = (
                f"Order #{data['order_id']} "
                f"has been created."
            )

            entity_id = data[
                "order_id"
            ]

            notification_type = (
                Notification.TYPE_ORDER_CREATED
            )

        elif event_type == "payment.succeeded":

            # این event فعلاً user_id ندارد.
            # در نسخه بعدی می‌توانیم user_id
            # را در payment.succeeded اضافه کنیم.

            return

        elif event_type == "payment.failed":

            return

        elif event_type == "order.cancelled":

            return

        else:

            raise ValueError(
                f"Unknown event: {event_type}"
            )

        Notification.objects.create(
            user_id=user_id,
            notification_type=notification_type,
            channel=Notification.CHANNEL_IN_APP,
            title=title,
            message=message,
            entity_id=entity_id,
        )

        ProcessedEvent.objects.create(
            event_id=event_id,
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
                f"Notification failed: {exc}"
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
                "Notification consumer started..."
            )

            channel.start_consuming()

        except Exception as exc:

            print(
                f"Connection failed: {exc}"
            )

            time.sleep(5)