import requests

from django.conf import settings


class InventoryServiceError(Exception):
    pass


class InventoryClient:

    def __init__(self):
        self.base_url = settings.INVENTORY_SERVICE_URL

    def reserve(
        self,
        product_id,
        quantity,
    ):
        url = (
            f"{self.base_url}"
            "/api/inventory/reserve/"
        )

        payload = {
            "product_id": product_id,
            "quantity": quantity,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=5,
            )

        except requests.RequestException as exc:
            raise InventoryServiceError(
                "Inventory service is unavailable."
            ) from exc

        if response.status_code == 404:
            raise InventoryServiceError(
                "Inventory does not exist for this product."
            )

        if response.status_code == 409:
            raise InventoryServiceError(
                "Not enough inventory."
            )

        if response.status_code != 200:
            raise InventoryServiceError(
                "Inventory reservation failed."
            )

        return response.json()

    def release(
        self,
        product_id,
        quantity,
    ):
        url = (
            f"{self.base_url}"
            "/api/inventory/release/"
        )

        payload = {
            "product_id": product_id,
            "quantity": quantity,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=5,
            )

        except requests.RequestException as exc:
            raise InventoryServiceError(
                "Inventory service is unavailable."
            ) from exc

        if response.status_code == 404:
            raise InventoryServiceError(
                "Inventory does not exist for this product."
            )

        if response.status_code == 409:
            raise InventoryServiceError(
                "Inventory release failed."
            )

        if response.status_code != 200:
            raise InventoryServiceError(
                "Inventory release failed."
            )

        return response.json()