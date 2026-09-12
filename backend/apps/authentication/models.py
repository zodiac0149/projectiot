import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class GoogleOAuthToken(models.Model):
    """
    Stores Google OAuth credentials per user for Calendar API synchronization.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="google_token")
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    token_uri = models.CharField(max_length=255, default="https://oauth2.googleapis.com/token")
    client_id = models.CharField(max_length=255, blank=True, null=True)
    client_secret = models.CharField(max_length=255, blank=True, null=True)
    scopes = models.TextField(default="https://www.googleapis.com/auth/calendar.readonly")
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return timezone.now() >= self.expires_at

    def __str__(self) -> str:
        return f"GoogleOAuthToken(user={self.user.username})"
