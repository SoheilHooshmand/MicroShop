from django.core.management.base import BaseCommand

from inventory.consumers import consume


class Command(BaseCommand):

    help = "Consume RabbitMQ events"

    def handle(
        self,
        *args,
        **options,
    ):

        self.stdout.write(
            self.style.SUCCESS(
                "Inventory consumer started..."
            )
        )

        consume()