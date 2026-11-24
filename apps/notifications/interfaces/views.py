from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.crm.infrastructure.models import Lead
from apps.notifications.infrastructure.models import FollowUpStatus, FollowUpTask, Notification
from apps.users.interfaces.permissions import IsStaffOrAgent, is_admin

from .serializers import (
    FollowUpCreateSerializer,
    FollowUpTaskSerializer,
    NotificationCountSerializer,
    NotificationSerializer,
)

TAG = ["Notifications"]


@extend_schema(
    tags=TAG,
    summary="Mes notifications",
    parameters=[OpenApiParameter("unread", bool, description="1 = non lues seulement")],
)
class NotificationListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        if self.request.query_params.get("unread") in ("1", "true"):
            qs = qs.filter(read_at__isnull=True)
        return qs


@extend_schema(tags=TAG, summary="Nombre de notifications non lues", responses={200: NotificationCountSerializer})
class NotificationUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"unread": Notification.objects.filter(user=request.user, read_at__isnull=True).count()})


@extend_schema(
    tags=TAG, summary="Marquer une notification comme lue", request=None, responses={200: NotificationSerializer}
)
class NotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        n = get_object_or_404(Notification, id=id, user=request.user)
        if n.read_at is None:
            n.read_at = timezone.now()
            n.save(update_fields=["read_at"])
        return Response(NotificationSerializer(n).data)


@extend_schema(tags=TAG, summary="Tout marquer comme lu", request=None, responses={200: NotificationCountSerializer})
class NotificationReadAllView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, read_at__isnull=True).update(read_at=timezone.now())
        return Response({"unread": 0})


@extend_schema(tags=TAG)
class FollowUpListView(generics.ListCreateAPIView):
    permission_classes = [IsStaffOrAgent]
    serializer_class = FollowUpTaskSerializer

    def get_queryset(self):
        qs = FollowUpTask.objects.select_related("lead", "assigned_to").filter(status=FollowUpStatus.OUVERTE)
        return qs if is_admin(self.request.user) else qs.filter(assigned_to=self.request.user)

    @extend_schema(summary="Tâches de relance (équipe) : les miennes, ou toutes pour un administrateur")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Planifier une relance sur un prospect",
        request=FollowUpCreateSerializer,
        responses={201: FollowUpTaskSerializer},
    )
    def post(self, request, *args, **kwargs):
        s = FollowUpCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        lead = get_object_or_404(Lead, id=d["lead"])
        # Le conseiller qui planifie s'en charge ; un administrateur planifie pour le conseiller du prospect (sinon pour lui).
        owner = lead.assigned_agent if (is_admin(request.user) and lead.assigned_agent_id) else request.user
        task = FollowUpTask.objects.create(
            lead=lead, assigned_to=owner, reason=d["reason"], due_date=d.get("due_date") or timezone.localdate()
        )
        return Response(FollowUpTaskSerializer(task).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=TAG, summary="Marquer une relance comme faite", request=None, responses={200: FollowUpTaskSerializer}
)
class FollowUpDoneView(APIView):
    permission_classes = [IsStaffOrAgent]

    def post(self, request, id):
        qs = FollowUpTask.objects.select_related("lead", "assigned_to")
        task = get_object_or_404(qs if is_admin(request.user) else qs.filter(assigned_to=request.user), id=id)
        if task.status != FollowUpStatus.FAITE:
            task.status = FollowUpStatus.FAITE
            task.completed_at = timezone.now()
            task.save(update_fields=["status", "completed_at"])
        return Response(FollowUpTaskSerializer(task).data)
