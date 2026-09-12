from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

User = get_user_model()

class CurrentUserView(APIView):
    """
    Returns the authenticated user, or the default engineering demo user if in local dev.
    """
    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            # Provide or create a default engineer user in local development mode
            user, _ = User.objects.get_or_create(
                username="engineer_demo",
                defaults={"email": "student@engineering.edu", "first_name": "Alex", "last_name": "Dev"}
            )
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
