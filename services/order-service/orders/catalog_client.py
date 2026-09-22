import requests
from django.conf import settings


class CatalogServiceError(Exception):
    pass


class CatalogClient:

    def __init__(self):
        self.base_url = settings.CATALOG_SERVICE_URL
        self.token = settings.CATALOG_SERVICE_TOKEN

    def get_product(self, product_id):

        url = f"{self.base_url}/internal/catalog/products/{product_id}/"

        headers = {
            "X-Service-Name": "order-service",
            "X-Service-Token": self.token,
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=5,
            )

        except requests.RequestException as exc:
            raise CatalogServiceError(
                "Catalog service is unavailable"
            ) from exc

        if response.status_code == 404:
            raise CatalogServiceError(
                "Product does not exist"
            )

        if response.status_code in (401, 403):
            raise CatalogServiceError(
                "Order service is not authorized to access Catalog service"
            )

        if response.status_code != 200:
            raise CatalogServiceError(
                "Catalog service returned an error"
            )

        return response.json()