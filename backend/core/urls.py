from django.contrib import admin
from django.urls import path, include
from rest_framework.response import Response
from rest_framework.views import APIView

class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "study-planner-core",
            "version": "1.0.0"
        })

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthCheckView.as_view(), name="health_check"),
    path("api/auth/", include("apps.authentication.urls")),
    path("api/calendar/", include("apps.calendar_sync.urls")),
    path("api/scheduler/", include("apps.scheduler.urls")),
]
