"""Back-office : performance de chaque conseiller (portefeuille, ventes, relances en retard)."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.crm.domain.lead_service import rescore
from apps.crm.infrastructure.models import CRMSettings, Lead, PipelineStage
from apps.crm.interfaces.serializers import CRMSettingsSerializer
from apps.notifications.infrastructure.models import FollowUpStatus, FollowUpTask
from apps.users.infrastructure.models import UserRole
from apps.users.interfaces.permissions import IsAdminRole

User = get_user_model()

AdvisorPerformanceSchema = inline_serializer(
    "AdvisorPerformance",
    {
        "id": serializers.IntegerField(),
        "name": serializers.CharField(),
        "email": serializers.EmailField(),
        "is_active": serializers.BooleanField(),
        "leads_total": serializers.IntegerField(),
        "leads_active": serializers.IntegerField(),
        "leads_new_period": serializers.IntegerField(),
        "sales": serializers.IntegerField(),
        "sales_amount": serializers.DecimalField(max_digits=16, decimal_places=2),
        "lost": serializers.IntegerField(),
        "conversion_rate": serializers.FloatField(),
        "followups_open": serializers.IntegerField(),
        "followups_overdue": serializers.IntegerField(),
    },
    many=True,
)


@extend_schema(
    tags=["Back-office Utilisateurs"],
    summary="Performance par conseiller (portefeuille, ventes, relances en retard)",
    parameters=[OpenApiParameter("days", int, description="Fenêtre en jours (défaut 30)")],
    responses={200: AdvisorPerformanceSchema},
)
class AdvisorPerformanceView(APIView):
    """`?days=` (défaut 30) : fenêtre des « nouveaux prospects » et des ventes comptées."""

    permission_classes = [IsAdminRole]

    def get(self, request):
        try:
            days = min(max(int(request.query_params.get("days", 30)), 1), 366)
        except ValueError:
            days = 30
        since = timezone.now() - timedelta(days=days)
        today = timezone.localdate()

        rows = []
        for u in User.objects.filter(role=UserRole.AGENT).order_by("first_name", "last_name"):
            leads = Lead.objects.filter(assigned_agent=u)
            agg = leads.aggregate(
                total=Count("id"),
                active=Count("id", filter=~Q(stage__in=[PipelineStage.VENTE, PipelineStage.PERDU])),
                new=Count("id", filter=Q(created_at__gte=since)),
                lost=Count("id", filter=Q(stage=PipelineStage.PERDU)),
                sales=Count("id", filter=Q(stage=PipelineStage.VENTE, converted_at__gte=since)),
                amount=Sum("budget", filter=Q(stage=PipelineStage.VENTE, converted_at__gte=since)),
            )
            closed = agg["sales"] + agg["lost"]
            tasks = FollowUpTask.objects.filter(assigned_to=u, status=FollowUpStatus.OUVERTE)
            rows.append(
                {
                    "id": u.id,
                    "name": u.get_full_name() or u.email,
                    "email": u.email,
                    "is_active": u.is_active,
                    "leads_total": agg["total"],
                    "leads_active": agg["active"],
                    "leads_new_period": agg["new"],
                    "sales": agg["sales"],
                    "sales_amount": agg["amount"] or 0,
                    "lost": agg["lost"],
                    "conversion_rate": round(agg["sales"] * 100 / closed, 1) if closed else 0.0,
                    "followups_open": tasks.count(),
                    "followups_overdue": tasks.filter(due_date__lt=today).count(),
                }
            )
        rows.sort(key=lambda r: (-r["sales"], -r["leads_active"]))
        return Response(rows)


@extend_schema(tags=["Back-office CRM"], summary="Réglages commerciaux (score, seuils, relances)")
class CRMSettingsView(generics.RetrieveUpdateAPIView):
    """GET : réglages actuels. PATCH : modification (administrateur). Les scores existants ne changent qu'au recalcul."""

    permission_classes = [IsAdminRole]
    serializer_class = CRMSettingsSerializer

    def get_object(self):
        return CRMSettings.load()


@extend_schema(
    tags=["Back-office CRM"],
    summary="Recalcule le score de tous les prospects avec les réglages actuels",
    request=None,
    responses={200: inline_serializer("RescoreResult", {"updated": serializers.IntegerField()})},
)
class RescoreAllLeadsView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        n = 0
        for lead in Lead.objects.all().iterator():
            before = (lead.score, lead.temperature)
            rescore(lead)
            if (lead.score, lead.temperature) != before:
                Lead.objects.filter(pk=lead.pk).update(score=lead.score, temperature=lead.temperature)
                n += 1
        return Response({"updated": n})
