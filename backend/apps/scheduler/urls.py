from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet,
    FixedEventViewSet,
    StudySessionViewSet,
    ReshuffleScheduleView,
    PurgeExpiredView
)

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"fixed-events", FixedEventViewSet, basename="fixed-event")
router.register(r"sessions", StudySessionViewSet, basename="session")

urlpatterns = [
    path("", include(router.urls)),
    path("reshuffle/", ReshuffleScheduleView.as_view(), name="reshuffle_schedule"),
    path("purge-expired/", PurgeExpiredView.as_view(), name="purge_expired"),
]
