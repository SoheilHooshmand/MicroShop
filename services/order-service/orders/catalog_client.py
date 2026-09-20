import requests
from django.conf import settings

class CatalogServiceError(Exception):
    pass


class CatalogClient:

    def __init__(self):
        self.base_url = settings.CATALOG_SERVICE_URL

    def get_product(self, product_id):
        url = (
            f"{self.base_url}/api/catalog/products/"
            f"{product_id}/"
        )

        try:
            response = requests.get(
                url,
                timeout=5
            )
        except requests.RequestException as exc:
            raise CatalogServiceError(
                "Catalog service is unavailable",
            ) from exc

        if response.status_code == 404:
            raise CatalogServiceError(
                "Product does not exist",
            )

        if response.status_code != 200:
            raise CatalogServiceError(
                "Catalog service returned an error",
            )

        return response.json()
