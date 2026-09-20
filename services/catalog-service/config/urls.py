"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from products.views import (
    CategoryListCreateView,
    CategoryDetailView,
    ProductListCreateView,
    ProductDetailView,
    health_check,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Categories
    path(
        "api/catalog/categories/",
        CategoryListCreateView.as_view(),
        name="category-list",
    ),
    path(
        "api/catalog/categories/<int:pk>/",
        CategoryDetailView.as_view(),
        name="category-detail",
    ),

    # Products
    path(
        "api/catalog/products/",
        ProductListCreateView.as_view(),
        name="product-list",
    ),
    path(
        "api/catalog/products/<int:pk>/",
        ProductDetailView.as_view(),
        name="product-detail",
    ),

    # Health
    path("health/", health_check, name="health-check"),
]