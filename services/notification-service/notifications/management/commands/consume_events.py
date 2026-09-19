from django.core.management.base import BaseCommand

from notifications.consumers import consume


class Command(BaseCommand):

    help = "Consume RabbitMQ events"

    def handle(
        self,
        *args,
        **options,
    ):

        self.stdout.write(
            self.style.SUCCESS(
                "Notification consumer started..."
            )
        )

        consume()