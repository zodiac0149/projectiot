from django.urls import path
from .views import (
    TriggerSyncView,
    GoogleOAuthLoginView,
    GoogleOAuthCallbackView,
    GoogleOAuthStatusView,
    GoogleOAuthDisconnectView,
)

urlpatterns = [
    path("sync/", TriggerSyncView.as_view(), name="calendar_sync_trigger"),
    path("oauth/login/", GoogleOAuthLoginView.as_view(), name="google_oauth_login"),
    path("oauth/callback/", GoogleOAuthCallbackView.as_view(), name="google_oauth_callback"),
    path("oauth/status/", GoogleOAuthStatusView.as_view(), name="google_oauth_status"),
    path("oauth/disconnect/", GoogleOAuthDisconnectView.as_view(), name="google_oauth_disconnect"),
]

