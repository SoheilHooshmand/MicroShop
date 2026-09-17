from rest_framework import viewsets
from django.http import JsonResponse

from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductSerializer
)

def health_check(request):
    return JsonResponse({
        "status": "ok",
        "service": "catalog-service",
    })


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related(
        "category"
    ).all()

    serializer_class = ProductSerializer

