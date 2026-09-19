import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.events import publish_to_rabbitmq
from orders.models import OutboxEvent


class Command(BaseCommand):

    help = "Publish pending outbox events"

    def handle(
        self,
        *args,
        **options,
    ):

        self.stdout.write(
            self.style.SUCCESS(
                "Order outbox publisher started..."
            )
        )

        while True:

            events = (
                OutboxEvent.objects
                .filter(
                    published=False,
                    available_at__lte=timezone.now(),
                )
                .order_by("created_at")[:50]
            )

            if not events:

                time.sleep(2)

                continue

            for event in events:

                try:

                    publish_to_rabbitmq(
                        event
                    )

                    event.published = True

                    event.published_at = (
                        timezone.now()
                    )

                    event.save(
                        update_fields=[
                            "published",
                            "published_at",
                        ]
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Published "
                            f"{event.event_type} "
                            f"{event.event_id}"
                        )
                    )

                except Exception as exc:

                    event.attempts += 1

                    delay = min(
                        60
                        * (
                            2
                            ** min(
                                event.attempts,
                                5,
                            )
                        ),
                        300,
                    )

                    event.available_at = (
                        timezone.now()
                        + timedelta(
                            seconds=delay
                        )
                    )

                    event.last_error = str(
                        exc
                    )

                    event.save(
                        update_fields=[
                            "attempts",
                            "available_at",
                            "last_error",
                        ]
                    )

                    self.stderr.write(
                        self.style.ERROR(
                            f"Failed to publish "
                            f"{event.event_id}: "
                            f"{exc}"
                        )
                    )

            time.sleep(2)