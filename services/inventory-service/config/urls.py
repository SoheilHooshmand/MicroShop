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

from inventory.views import (
    InventoryCreateView,
    InventoryDetailView,
    ReserveInventoryView,
    ReleaseInventoryView,
    health_check,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path(
        "api/inventory/",
        InventoryCreateView.as_view(),
        name="inventory-create",
    ),

    path(
        "api/inventory/<int:product_id>/",
        InventoryDetailView.as_view(),
        name="inventory-detail",
    ),

    path(
        "api/inventory/reserve/",
        ReserveInventoryView.as_view(),
        name="inventory-reserve",
    ),

    path(
        "api/inventory/release/",
        ReleaseInventoryView.as_view(),
        name="inventory-release",
    ),

    path(
        "health/",
        health_check,
        name="health",
    ),
]
