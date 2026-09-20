from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .cache import (
    CATEGORY_CACHE_TTL,
    PRODUCT_CACHE_TTL,
    category_cache_key,
    category_list_cache_key,
    invalidate_category_cache,
    invalidate_product_cache,
    product_cache_key,
    product_list_cache_key,
)
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "service": "catalog-service",
    })


class CategoryListCreateView(APIView):

    def get(self, request):
        query_string = request.META.get("QUERY_STRING", "")
        cache_key = category_list_cache_key(query_string)

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        queryset = Category.objects.all().order_by("id")
        serializer = CategorySerializer(queryset, many=True)
        data = serializer.data

        cache.set(cache_key, data, CATEGORY_CACHE_TTL)
        return Response(data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            category = serializer.save()

        invalidate_category_cache(category.id)

        return Response(
            CategorySerializer(category).data,
            status=status.HTTP_201_CREATED,
        )


class CategoryDetailView(APIView):

    def get(self, request, pk):
        cache_key = category_cache_key(pk)

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CategorySerializer(category)
        data = serializer.data

        cache.set(cache_key, data, CATEGORY_CACHE_TTL)
        return Response(data)

    def put(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CategorySerializer(category, data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        category = serializer.save()
        invalidate_category_cache(category.id)

        return Response(CategorySerializer(category).data)

    def patch(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CategorySerializer(
            category,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        category = serializer.save()
        invalidate_category_cache(category.id)

        return Response(CategorySerializer(category).data)

    def delete(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        category.delete()
        invalidate_category_cache(pk)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductListCreateView(APIView):

    def get(self, request):
        query_string = request.META.get("QUERY_STRING", "")
        cache_key = product_list_cache_key(query_string)

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        queryset = (
            Product.objects
            .select_related("category")
            .all()
            .order_by("id")
        )

        serializer = ProductSerializer(queryset, many=True)
        data = serializer.data

        cache.set(cache_key, data, PRODUCT_CACHE_TTL)
        return Response(data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            product = serializer.save()

        invalidate_product_cache(product.id)

        return Response(
            ProductSerializer(product).data,
            status=status.HTTP_201_CREATED,
        )


class ProductDetailView(APIView):

    def get(self, request, pk):
        cache_key = product_cache_key(pk)

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        try:
            product = (
                Product.objects
                .select_related("category")
                .get(pk=pk)
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductSerializer(product)
        data = serializer.data

        cache.set(cache_key, data, PRODUCT_CACHE_TTL)
        return Response(data)

    def put(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductSerializer(product, data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = serializer.save()
        invalidate_product_cache(product.id)

        return Response(ProductSerializer(product).data)

    def patch(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True,
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = serializer.save()
        invalidate_product_cache(product.id)

        return Response(ProductSerializer(product).data)

    def delete(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        product.delete()
        invalidate_product_cache(pk)

        return Response(status=status.HTTP_204_NO_CONTENT)