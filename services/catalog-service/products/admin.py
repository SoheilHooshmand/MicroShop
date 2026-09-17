from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "slug",
        "created_at",
    ]

    search_fields = [
        "name",
        "slug",
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "category",
        "price",
        "is_active",
        "created_at",
    ]

    list_filter = [
        "is_active",
        "category",
    ]

    search_fields = [
        "name",
        "slug",
    ]