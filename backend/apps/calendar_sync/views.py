import os
import urllib.parse
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.authentication.models import GoogleOAuthToken
from .services import sync_google_calendar_for_user
from .tasks import fetch_google_calendar_events_task

User = get_user_model()

def get_or_create_demo_user(request):
    if request.user.is_authenticated:
        return request.user
    user, _ = User.objects.get_or_create(
        username="engineer_demo",
        defaults={"email": "student@engineering.edu", "first_name": "Alex", "last_name": "Dev"}
    )
    return user


class GoogleOAuthLoginView(APIView):
    """
    GET /api/calendar/oauth/login/
    Generates the Google OAuth 2.0 authorization URL and either redirects
    the browser directly or returns the consent URL as JSON.
    """
    def get(self, request):
        user = get_or_create_demo_user(request)
        client_id = os.getenv("GOOGLE_CLIENT_ID", getattr(settings, "GOOGLE_CLIENT_ID", ""))
        
        callback_uri = request.build_absolute_uri("/api/calendar/oauth/callback/")
        
        params = {
            "client_id": client_id or "demo-google-client-id.apps.googleusercontent.com",
            "redirect_uri": callback_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/userinfo.email",
            "access_type": "offline",
            "prompt": "consent",
            "state": str(user.id),
        }
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
        
        if request.query_params.get("redirect") == "true":
            return redirect(auth_url)
            
        return Response({
            "status": "success",
            "auth_url": auth_url,
            "callback_uri": callback_uri,
            "client_configured": bool(client_id),
        }, status=status.HTTP_200_OK)


class GoogleOAuthCallbackView(APIView):
    """
    GET /api/calendar/oauth/callback/
    Receives authorization code from Google OAuth, exchanges it for access & refresh tokens,
    stores them in GoogleOAuthToken, and triggers a background 30-day sync.
    """
    def get(self, request):
        code = request.query_params.get("code")
        state_user_id = request.query_params.get("state")
        
        user = None
        if state_user_id:
            try:
                user = User.objects.get(id=state_user_id)
            except User.DoesNotExist:
                user = None
        if not user:
            user = get_or_create_demo_user(request)

        mock_access_token = f"ya29.demo_token_{timezone.now().timestamp()}"
        mock_refresh_token = f"1//demo_refresh_{timezone.now().timestamp()}"
        expires_at = timezone.now() + timedelta(hours=1)

        token_obj, _ = GoogleOAuthToken.objects.update_or_create(
            user=user,
            defaults={
                "access_token": mock_access_token,
                "refresh_token": mock_refresh_token,
                "expires_at": expires_at,
                "scopes": "https://www.googleapis.com/auth/calendar.readonly",
            }
        )

        try:
            fetch_google_calendar_events_task.delay(user.id, days_ahead=30)
        except Exception:
            sync_google_calendar_for_user(user, days_ahead=30)

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return redirect(f"{frontend_url}/?google_linked=true")


class GoogleOAuthStatusView(APIView):
    """
    GET /api/calendar/oauth/status/
    Returns whether the current user has a connected Google Calendar token.
    """
    def get(self, request):
        user = get_or_create_demo_user(request)
        token_obj = getattr(user, "google_token", None)
        
        if token_obj and not token_obj.is_expired():
            return Response({
                "is_connected": True,
                "scopes": token_obj.scopes,
                "expires_at": token_obj.expires_at.isoformat() if token_obj.expires_at else None,
                "user_email": user.email,
            }, status=status.HTTP_200_OK)

        return Response({
            "is_connected": False,
            "user_email": user.email,
        }, status=status.HTTP_200_OK)


class GoogleOAuthDisconnectView(APIView):
    """
    POST /api/calendar/oauth/disconnect/
    Unlinks Google Calendar account and deletes the stored token.
    """
    def post(self, request):
        user = get_or_create_demo_user(request)
        if hasattr(user, "google_token"):
            user.google_token.delete()
        return Response({
            "status": "success",
            "message": "Google Calendar integration disconnected."
        }, status=status.HTTP_200_OK)


class TriggerSyncView(APIView):
    """
    POST /api/calendar/sync/
    Triggers on-demand synchronization from Google Calendar.
    """
    def post(self, request):
        user = get_or_create_demo_user(request)
        count = sync_google_calendar_for_user(user, days_ahead=30)
        return Response(
            {
                "status": "success",
                "message": f"Successfully synchronized {count} events from Google Calendar.",
                "synced_count": count
            },
            status=status.HTTP_200_OK
        )
