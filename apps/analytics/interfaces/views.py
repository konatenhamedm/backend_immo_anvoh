from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.application import reporting
from apps.analytics.application.recorder import record
from apps.users.interfaces.permissions import IsAdminRole
from apps.users.interfaces.throttling import ScopedThrottleMixin

from .serializers import EventBatchSerializer


@extend_schema(
    tags=["Statistiques"],
    summary="Envoi d'événements de mesure par le navigateur (lot de 20 au plus)",
    description="Public. Liste fermée d'événements ; aucune donnée personnelle acceptée (e-mail, téléphone, nom… sont supprimés).",
    request=EventBatchSerializer,
    responses={204: None},
)
class EventIngestView(ScopedThrottleMixin, APIView):
    throttle_scope = "analytics"
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = EventBatchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        for e in s.validated_data["events"]:
            record(
                e["name"],
                user=request.user,
                anonymous_id=s.validated_data["anonymous_id"],
                channel=e.get("channel", ""),
                path=e.get("path", ""),
                properties=e.get("properties"),
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Statistiques"],
    summary="Tableau de bord d'acquisition : KPI, entonnoir, ROI par canal (administrateurs)",
    parameters=[OpenApiParameter("days", int, description="Période en jours (1 à 365, défaut 30)")],
    responses={200: OpenApiTypes.OBJECT},
)
class AnalyticsSummaryView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        try:
            days = max(1, min(365, int(request.query_params.get("days", 30))))
        except ValueError:
            days = 30
        return Response(reporting.summary(days))
