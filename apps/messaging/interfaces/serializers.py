from rest_framework import serializers

from apps.messaging.infrastructure.models import Conversation, Message


def user_brief(user):
    if user is None:
        return None
    name = f"{user.first_name} {user.last_name}".strip() or user.email
    return {'id': user.id, 'name': name, 'role': user.role, 'role_display': user.get_role_display()}


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'is_mine', 'body', 'created_at']

    def get_sender(self, obj):
        return user_brief(obj.sender)

    def get_is_mine(self, obj) -> bool:
        request = self.context.get('request')
        return bool(request and obj.sender_id == request.user.id)


class ConversationSerializer(serializers.ModelSerializer):
    property = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'subject', 'property', 'participants', 'last_message', 'unread_count', 'updated_at']

    def get_property(self, obj):
        p = obj.property
        return {'id': str(p.id), 'reference': p.reference, 'title': p.title, 'slug': p.slug} if p else None

    def get_participants(self, obj):
        me = self.context['request'].user.id
        return [user_brief(cp.user) for cp in obj.participants.all() if cp.user_id != me]

    def get_last_message(self, obj):
        messages = list(obj.messages.all())
        return MessageSerializer(messages[-1], context=self.context).data if messages else None

    def get_unread_count(self, obj) -> int:
        me = self.context['request'].user.id
        mine = next((cp for cp in obj.participants.all() if cp.user_id == me), None)
        return sum(
            1 for m in obj.messages.all()
            if m.sender_id != me and (mine is None or mine.last_read_at is None or m.created_at > mine.last_read_at)
        )


class StartConversationSerializer(serializers.Serializer):
    property_id = serializers.UUIDField(required=False)
    recipient_id = serializers.IntegerField(required=False)
    subject = serializers.CharField(required=False, allow_blank=True, max_length=200)
    body = serializers.CharField(max_length=5000)


class NewMessageSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000)
