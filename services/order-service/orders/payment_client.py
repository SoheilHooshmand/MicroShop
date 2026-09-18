import requests

from django.conf import settings


class PaymentServiceError(Exception):
    pass


class PaymentClient:

    def __init__(self):
        self.base_url = settings.PAYMENT_SERVICE_URL

    def create_payment(
        self,
        order_id,
        user_id,
        amount,
    ):
        url = (
            f"{self.base_url}"
            "/api/payments/"
        )

        payload = {
            "order_id": order_id,
            "user_id": user_id,
            "amount": str(amount),
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=5,
            )

        except requests.RequestException as exc:
            raise PaymentServiceError(
                "Payment service is unavailable."
            ) from exc

        if response.status_code == 409:
            raise PaymentServiceError(
                "Payment already exists for this order."
            )

        if response.status_code != 201:
            raise PaymentServiceError(
                "Payment creation failed."
            )

        return response.json()