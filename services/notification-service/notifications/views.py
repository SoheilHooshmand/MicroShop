from django.http import JsonResponse
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import (
    NotificationCreateSerializer,
    NotificationSerializer,
)


class NotificationCreateView(APIView):

    def post(self, request):

        serializer = NotificationCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        notification = Notification.objects.create(
            **serializer.validated_data
        )

        return Response(
            NotificationSerializer(
                notification
            ).data,
            status=status.HTTP_201_CREATED,
        )


class NotificationListView(
    generics.ListAPIView
):

    serializer_class = NotificationSerializer

    def get_queryset(self):

        queryset = Notification.objects.all()

        user_id = self.request.query_params.get(
            "user_id"
        )

        if user_id:
            queryset = queryset.filter(
                user_id=user_id
            )

        return queryset.order_by("-created_at")


class NotificationDetailView(
    generics.RetrieveAPIView
):

    queryset = Notification.objects.all()

    serializer_class = NotificationSerializer


class NotificationMarkAsSentView(APIView):

    def post(self, request, pk):

        try:
            notification = Notification.objects.get(
                pk=pk
            )

        except Notification.DoesNotExist:
            return Response(
                {
                    "detail": (
                        "Notification not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if notification.status == (
            Notification.STATUS_SENT
        ):
            return Response(
                NotificationSerializer(
                    notification
                ).data
            )

        notification.status = (
            Notification.STATUS_SENT
        )

        notification.sent_at = timezone.now()

        notification.save(
            update_fields=[
                "status",
                "sent_at",
                "updated_at",
            ]
        )

        return Response(
            NotificationSerializer(
                notification
            ).data
        )


def health_check(request):

    return JsonResponse(
        {
            "status": "ok",
            "service": "notification-service",
        }
    )