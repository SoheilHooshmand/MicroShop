from django.urls import path

from .views import (
    PaymentCreateView,
    PaymentDetailView,
    PaymentFailedView,
    PaymentSuccessView,
)


urlpatterns = [
    path(
        "",
        PaymentCreateView.as_view(),
        name="payment-create",
    ),

    path(
        "<int:pk>/",
        PaymentDetailView.as_view(),
        name="payment-detail",
    ),

    path(
        "<int:pk>/success/",
        PaymentSuccessView.as_view(),
        name="payment-success",
    ),

    path(
        "<int:pk>/failed/",
        PaymentFailedView.as_view(),
        name="payment-failed",
    ),
]