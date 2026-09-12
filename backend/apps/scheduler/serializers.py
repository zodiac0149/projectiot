from rest_framework import serializers
from django.utils import timezone
from .models import Task, FixedEvent, StudySession

class TaskSerializer(serializers.ModelSerializer):
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "priority",
            "estimated_minutes",
            "deadline",
            "cognitive_load",
            "status",
            "is_deleted",
            "is_expired",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_deleted", "is_expired", "created_at", "updated_at"]

    def get_is_expired(self, obj) -> bool:
        return obj.deadline < timezone.now() and obj.status != Task.Status.COMPLETED

    def validate_priority(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Priority must be between 1 and 5.")
        return value

    def validate_estimated_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError("Estimated duration must be greater than 0 minutes.")
        return value


class FixedEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = FixedEvent
        fields = [
            "id",
            "google_event_id",
            "title",
            "start_time",
            "end_time",
            "is_holiday",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        start = data.get("start_time")
        end = data.get("end_time")
        if start and end and end <= start:
            raise serializers.ValidationError({"end_time": "End time must be strictly after start time."})
        return data


class StudySessionSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="task.title", read_only=True)
    task_priority = serializers.IntegerField(source="task.priority", read_only=True)
    task_cognitive_load = serializers.CharField(source="task.cognitive_load", read_only=True)

    class Meta:
        model = StudySession
        fields = [
            "id",
            "task",
            "task_title",
            "task_priority",
            "task_cognitive_load",
            "start_time",
            "end_time",
            "status",
            "rationale",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ReshuffleTriggerSerializer(serializers.Serializer):
    disruption_context = serializers.CharField(
        required=False,
        default="User triggered schedule re-optimization",
        max_length=500
    )
    horizon_days = serializers.IntegerField(
        required=False,
        default=7,
        min_value=1,
        max_value=30
    )
