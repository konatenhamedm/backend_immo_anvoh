from rest_framework import serializers

from apps.analytics.domain.events import CLIENT_EVENTS
from apps.crm.infrastructure.models import AcquisitionChannel


class ClientEventSerializer(serializers.Serializer):
    name = serializers.ChoiceField(choices=sorted(CLIENT_EVENTS))
    path = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    channel = serializers.ChoiceField(choices=AcquisitionChannel.choices, required=False, allow_blank=True, default="")
    properties = serializers.DictField(required=False, default=dict)


class EventBatchSerializer(serializers.Serializer):
    anonymous_id = serializers.RegexField(r"^[A-Za-z0-9_-]{8,64}$", help_text="Identifiant aléatoire du navigateur")
    events = ClientEventSerializer(many=True, allow_empty=False, max_length=20)
