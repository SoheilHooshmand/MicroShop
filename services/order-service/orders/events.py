import json
import os
from datetime import datetime, timezone

import pika

from .models import OutboxEvent


EXCHANGE_NAME = "microshop.events"


def create_outbox_event(
    event_type,
    data,
):
    return OutboxEvent.objects.create(
        event_type=event_type,
        payload={
            "event_id": None,
            "event_type": event_type,
            "occurred_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "source": "order-service",
            "retry_count": 0,
            "data": data,
        },
    )


def get_rabbitmq_connection():

    rabbitmq_url = os.getenv(
        "RABBITMQ_URL",
        "amqp://microshop:rabbitmq_password@localhost:5672/%2F",
    )

    parameters = pika.URLParameters(
        rabbitmq_url
    )

    return pika.BlockingConnection(
        parameters
    )


def publish_to_rabbitmq(event):

    connection = get_rabbitmq_connection()

    try:

        channel = connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type="topic",
            durable=True,
        )

        channel.confirm_delivery()

        payload = event.payload.copy()

        payload["event_id"] = str(
            event.event_id
        )

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=event.event_type,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                message_id=str(event.event_id),
            ),
            mandatory=True,
        )

    finally:
        connection.close()