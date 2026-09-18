import json
import os
import uuid

import pika


EXCHANGE_NAME = "microshop.events"


def publish_event(event_type, data):
    rabbitmq_url = os.getenv(
        "RABBITMQ_URL",
        "amqp://microshop:rabbitmq_password@localhost:5672/%2F",
    )

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "data": data,
    }

    connection = pika.BlockingConnection(
        pika.URLParameters(rabbitmq_url)
    )

    try:
        channel = connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type="topic",
            durable=True,
        )

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=event_type,
            body=json.dumps(event),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                content_type="application/json",
            ),
        )
    finally:
        connection.close()