from django.core.management.base import BaseCommand

from payments.consumers import consume


class Command(BaseCommand):

    help = "Consume RabbitMQ events"

    def handle(
        self,
        *args,
        **options,
    ):

        consume()