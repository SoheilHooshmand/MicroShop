from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
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

