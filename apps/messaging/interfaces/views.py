from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.messaging.infrastructure.models import Conversation, ConversationParticipant, Message
from apps.properties.infrastructure.models import Property
from apps.users.infrastructure.models import User, UserRole
from apps.users.interfaces.permissions import is_notary, is_staff_or_agent

from .schemas import UnreadCountSchema
from .serializers import ConversationSerializer, MessageSerializer, NewMessageSerializer, StartConversationSerializer


def _my_conversations(user):
    return (
        Conversation.objects.filter(participants__user=user)
        .select_related("property")
        .prefetch_related(
            Prefetch("participants", queryset=ConversationParticipant.objects.select_related("user")), "messages"
        )
        .distinct()
    )


def _team_contact():
    """Interlocuteur par défaut côté Thiebbro : un conseiller actif, sinon un administrateur."""
    return (
        User.objects.filter(is_active=True, role=UserRole.AGENT).order_by("id").first()
        or User.objects.filter(is_active=True, role=UserRole.ADMIN).order_by("id").first()
        or User.objects.filter(is_active=True, is_staff=True).order_by("id").first()
    )


def _resolve_recipient(sender, prop, recipient_id):
    """
    Qui peut écrire à qui :
    - à propos d'un bien → au propriétaire, sinon au conseiller du bien, sinon à l'équipe ;
    - l'équipe et les notaires peuvent écrire à n'importe quel compte ;
    - un client peut écrire à un membre de l'équipe ou à un notaire (pas à un autre client).
    """
    if recipient_id:
        recipient = get_object_or_404(User, id=recipient_id, is_active=True)
        allowed = (
            is_staff_or_agent(sender)
            or is_notary(sender)
            or recipient.role in (UserRole.AGENT, UserRole.ADMIN, UserRole.NOTAIRE)
            or recipient.is_staff
            or (prop is not None and recipient.id in (prop.owner_id, prop.assigned_agent_id))
        )
        if not allowed:
            return None, "Vous ne pouvez pas contacter ce compte directement."
        return recipient, None
    if prop is not None:
        return (prop.owner or prop.assigned_agent or _team_contact()), None
    return _team_contact(), None


@extend_schema(tags=["Messagerie"])
class ConversationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: ConversationSerializer(many=True)}, summary="Mes conversations")
    def get(self, request):
        qs = _my_conversations(request.user)
        return Response(ConversationSerializer(qs, many=True, context={"request": request}).data)

    @extend_schema(
        request=StartConversationSerializer,
        responses={201: ConversationSerializer},
        summary="Démarrer (ou reprendre) une conversation, éventuellement à propos d'un bien",
    )
    def post(self, request):
        serializer = StartConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        prop = get_object_or_404(Property, id=data["property_id"]) if data.get("property_id") else None
        recipient, error = _resolve_recipient(request.user, prop, data.get("recipient_id"))
        if error:
            return Response({"detail": error}, status=status.HTTP_403_FORBIDDEN)
        if recipient is None or recipient.id == request.user.id:
            return Response(
                {"detail": "Aucun interlocuteur disponible pour le moment."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Reprend la conversation existante entre ces deux personnes sur ce bien.
        existing = (
            Conversation.objects.filter(property=prop, participants__user=request.user)
            .filter(participants__user=recipient)
            .annotate(n=Count("participants", distinct=True))
            .filter(n=2)
            .first()
        )
        conversation = existing or Conversation.objects.create(
            property=prop, subject=data.get("subject") or (prop.title if prop else "Question à l'équipe Thiebbro")
        )
        if not existing:
            ConversationParticipant.objects.bulk_create(
                [
                    ConversationParticipant(conversation=conversation, user=request.user, last_read_at=timezone.now()),
                    ConversationParticipant(conversation=conversation, user=recipient),
                ]
            )
        Message.objects.create(conversation=conversation, sender=request.user, body=data["body"])
        conversation.save(update_fields=["updated_at"])
        conversation = _my_conversations(request.user).get(id=conversation.id)
        return Response(
            ConversationSerializer(conversation, context={"request": request}).data, status=status.HTTP_201_CREATED
        )


@extend_schema(tags=["Messagerie"])
class ConversationMessagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _membership(self, request, id):
        return get_object_or_404(
            ConversationParticipant.objects.select_related("conversation"), conversation_id=id, user=request.user
        )

    @extend_schema(
        responses={200: MessageSerializer(many=True)}, summary="Messages d'une conversation (les marque comme lus)"
    )
    def get(self, request, id):
        membership = self._membership(request, id)
        membership.last_read_at = timezone.now()
        membership.save(update_fields=["last_read_at"])
        messages = membership.conversation.messages.select_related("sender")
        return Response(MessageSerializer(messages, many=True, context={"request": request}).data)

    @extend_schema(request=NewMessageSerializer, responses={201: MessageSerializer}, summary="Envoyer un message")
    def post(self, request, id):
        membership = self._membership(request, id)
        serializer = NewMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = Message.objects.create(
            conversation=membership.conversation, sender=request.user, body=serializer.validated_data["body"]
        )
        membership.last_read_at = timezone.now()
        membership.save(update_fields=["last_read_at"])
        membership.conversation.save(update_fields=["updated_at"])
        return Response(MessageSerializer(message, context={"request": request}).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Messagerie"], summary="Nombre total de messages non lus (badge du menu)", responses={200: UnreadCountSchema}
)
class UnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = ConversationSerializer(_my_conversations(request.user), many=True, context={"request": request}).data
        return Response({"unread": sum(c["unread_count"] for c in data)})
