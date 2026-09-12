from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import GoogleOAuthToken

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    has_google_calendar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "has_google_calendar"]

    def get_has_google_calendar(self, obj) -> bool:
        return hasattr(obj, "google_token") and obj.google_token is not None

class GoogleOAuthTokenSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = GoogleOAuthToken
        fields = ["id", "scopes", "expires_at", "is_expired", "created_at", "updated_at"]
