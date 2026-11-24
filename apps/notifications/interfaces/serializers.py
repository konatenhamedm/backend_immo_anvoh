from rest_framework import serializers

from apps.notifications.infrastructure.models import FollowUpTask, Notification


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "kind", "title", "body", "url", "is_read", "created_at"]
        read_only_fields = fields

    def get_is_read(self, obj) -> bool:
        return obj.read_at is not None


class NotificationCountSerializer(serializers.Serializer):
    unread = serializers.IntegerField()


class FollowUpTaskSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source="lead.full_name", read_only=True)
    lead_phone = serializers.CharField(source="lead.phone_number", read_only=True)
    lead_stage = serializers.CharField(source="lead.stage", read_only=True)
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = FollowUpTask
        fields = [
            "id",
            "lead",
            "lead_name",
            "lead_phone",
            "lead_stage",
            "assigned_to",
            "assigned_to_name",
            "reason",
            "due_date",
            "status",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields

    def get_assigned_to_name(self, obj) -> str:
        return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip() if obj.assigned_to else ""
