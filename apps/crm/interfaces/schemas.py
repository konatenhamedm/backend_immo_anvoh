"""Schémas OpenAPI des réponses agrégées du module `crm` (documentation uniquement)."""

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

from apps.crm.infrastructure.models import PipelineStage
from apps.properties.interfaces.schemas import monthly_points

from .serializers import LeadKanbanItemSerializer


def _money():
    return serializers.DecimalField(max_digits=16, decimal_places=2)


AdminDashboardSchema = inline_serializer(
    "AdminDashboard",
    {
        "portfolio_value": _money(),
        "properties_for_sale": serializers.IntegerField(),
        "properties_total": serializers.IntegerField(),
        "active_leads": serializers.IntegerField(),
        "new_leads_this_month": serializers.IntegerField(),
        "visits_this_week": serializers.IntegerField(),
        "average_yield": serializers.FloatField(),
        "accreditations_pending": serializers.IntegerField(),
        "monthly_leads": monthly_points(),
        "funnel": inline_serializer(
            "FunnelStep",
            {
                "stage": serializers.CharField(),
                "label": serializers.CharField(),
                "count": serializers.IntegerField(),
                "pct": serializers.IntegerField(),
                "budget": _money(),
            },
            many=True,
        ),
        "activity": inline_serializer(
            "DashboardActivity",
            {
                "who": serializers.CharField(),
                "what": serializers.CharField(),
                "type": serializers.CharField(),
                "when": serializers.DateTimeField(),
            },
            many=True,
        ),
    },
)

_KanbanColumn = type(
    inline_serializer(
        "KanbanColumn",
        {
            "label": serializers.CharField(),
            "count": serializers.IntegerField(),
            "budget_total": _money(),
            "leads": LeadKanbanItemSerializer(many=True),
        },
    )
)

# Réponse du kanban : un objet dont les clés sont les codes d'étape du pipeline.
KanbanSchema = type("Kanban", (serializers.Serializer,), {code: _KanbanColumn() for code, _ in PipelineStage.choices})


GlobalSearchSchema = inline_serializer(
    "GlobalSearch",
    {
        "properties": inline_serializer(
            "SearchProperty",
            {
                "id": serializers.UUIDField(),
                "reference": serializers.CharField(),
                "title": serializers.CharField(),
                "slug": serializers.CharField(),
                "commune": serializers.CharField(),
                "status_display": serializers.CharField(),
            },
            many=True,
        ),
        "leads": inline_serializer(
            "SearchLead",
            {
                "id": serializers.UUIDField(),
                "full_name": serializers.CharField(),
                "phone_number": serializers.CharField(),
                "stage_display": serializers.CharField(),
            },
            many=True,
        ),
        "users": inline_serializer(
            "SearchUser",
            {
                "id": serializers.IntegerField(),
                "name": serializers.CharField(),
                "email": serializers.CharField(),
                "role_display": serializers.CharField(),
            },
            many=True,
        ),
    },
)
