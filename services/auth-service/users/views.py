from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.http import JsonResponse

from .serializers import RegistrationSerializer, UserSerializer


def health_check(request):
    return JsonResponse({
        "status": "ok"
    })

class RegistrationView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class VerifyTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        response = Response(
            {
                "authenticated": True,
                "user_id": request.user.id,
            }
        )

        response["X-User-ID"] = str(request.user.id)
        response["X-User-Email"] = request.user.email
        response["X-User-Staff"] = (
            "true" if request.user.is_staff else "false"
        )
        response["X-User-Admin"] = (
            "true" if request.user.is_superuser else "false"
        )

        return response