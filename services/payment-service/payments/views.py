from django.http import JsonResponse
from django.db import IntegrityError

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .serializers import (
    PaymentCreateSerializer,
    PaymentSerializer,
)


class PaymentCreateView(APIView):

    def post(self, request):

        serializer = PaymentCreateSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            payment = Payment.objects.create(
                order_id=data["order_id"],
                user_id=data["user_id"],
                amount=data["amount"],
                status=Payment.STATUS_PENDING,
            )

        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "Payment for this order "
                        "already exists."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )


class PaymentDetailView(APIView):

    def get(self, request, pk):

        try:
            payment = Payment.objects.get(pk=pk)

        except Payment.DoesNotExist:
            return Response(
                {
                    "detail": "Payment not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            PaymentSerializer(payment).data
        )


class PaymentSuccessView(APIView):

    def post(self, request, pk):

        try:
            payment = Payment.objects.get(pk=pk)

        except Payment.DoesNotExist:
            return Response(
                {
                    "detail": "Payment not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if payment.status != Payment.STATUS_PENDING:
            return Response(
                {
                    "detail": (
                        "Only pending payments "
                        "can be completed."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        payment.status = Payment.STATUS_SUCCESS

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            PaymentSerializer(payment).data
        )


class PaymentFailedView(APIView):

    def post(self, request, pk):

        try:
            payment = Payment.objects.get(pk=pk)

        except Payment.DoesNotExist:
            return Response(
                {
                    "detail": "Payment not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if payment.status != Payment.STATUS_PENDING:
            return Response(
                {
                    "detail": (
                        "Only pending payments "
                        "can be failed."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        payment.status = Payment.STATUS_FAILED

        payment.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            PaymentSerializer(payment).data
        )


def health_check(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "payment-service",
        }
    )