"""Back-office : tableau de bord commercial et recherche globale de l'en-tête."""

from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.crm.domain.lead_service import STAGE_ORDER
from apps.crm.infrastructure.models import (
    CRMInteraction,
    Lead,
    PipelineStage,
    VisitRequest,
    VisitRequestStatus,
)
from apps.properties.infrastructure.models import PUBLIC_STATUSES, Property, PropertyStatus, TransactionType
from apps.users.interfaces.permissions import IsStaffOrAgent

from ..schemas import AdminDashboardSchema, GlobalSearchSchema

MONTHS_FR = ["Janv.", "Févr.", "Mars", "Avr.", "Mai", "Juin", "Juil.", "Août", "Sept.", "Oct.", "Nov.", "Déc."]


@extend_schema(
    tags=["Back-office CRM"],
    summary="Tableau de bord commercial : portefeuille, prospects, visites, entonnoir, activité",
    responses={200: AdminDashboardSchema},
)
class AdminDashboardView(APIView):
    permission_classes = [IsStaffOrAgent]

    def get(self, request):
        from apps.accreditation.infrastructure.models import AccreditationFile, AccreditationStatus

        today = timezone.localdate()
        public = Property.objects.filter(status__in=PUBLIC_STATUSES)
        sales = public.filter(transaction=TransactionType.VENTE)
        leads = Lead.objects.all()
        active_leads = leads.exclude(stage__in=[PipelineStage.VENTE, PipelineStage.PERDU])
        week_end = today + timedelta(days=7 - today.weekday())

        start = (today.replace(day=1) - timedelta(days=150)).replace(day=1)
        per_month = {
            (d.year, d.month): n
            for d, n in leads.filter(created_at__date__gte=start)
            .annotate(m=TruncMonth("created_at"))
            .values("m")
            .annotate(n=Count("id"))
            .values_list("m", "n")
        }
        monthly, cursor = [], start
        while cursor <= today:
            monthly.append(
                {"month": MONTHS_FR[cursor.month - 1], "value": per_month.get((cursor.year, cursor.month), 0)}
            )
            cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

        # Entonnoir cumulatif : prospects ayant atteint au moins chaque étape (hors perdus).
        stage_rows = {
            r["stage"]: r
            for r in leads.exclude(stage=PipelineStage.PERDU)
            .values("stage")
            .annotate(n=Count("id"), budget=Sum("budget"))
        }
        total = sum(r["n"] for r in stage_rows.values()) or 0
        funnel = []
        for i, stage in enumerate(STAGE_ORDER):
            reached = [stage_rows[s] for s in STAGE_ORDER[i:] if s in stage_rows]
            n = sum(r["n"] for r in reached)
            funnel.append(
                {
                    "stage": stage,
                    "label": PipelineStage(stage).label,
                    "count": n,
                    "pct": round(n * 100 / total) if total else 0,
                    "budget": sum((r["budget"] or 0) for r in reached),
                }
            )

        activity = CRMInteraction.objects.select_related("lead").order_by("-created_at")[:8]
        return Response(
            {
                "portfolio_value": sales.aggregate(t=Sum("price"))["t"] or 0,
                "properties_for_sale": sales.count(),
                "properties_total": Property.objects.exclude(status="ARCHIVE").count(),
                "active_leads": active_leads.count(),
                "new_leads_this_month": leads.filter(
                    created_at__year=today.year, created_at__month=today.month
                ).count(),
                "visits_this_week": VisitRequest.objects.filter(scheduled_date__gte=today, scheduled_date__lt=week_end)
                .exclude(status=VisitRequestStatus.ANNULEE)
                .count(),
                "average_yield": round(
                    float(
                        public.exclude(estimated_yield_rate__isnull=True).aggregate(a=Avg("estimated_yield_rate"))["a"]
                        or 0
                    ),
                    2,
                ),
                "accreditations_pending": AccreditationFile.objects.filter(status=AccreditationStatus.EN_COURS).count(),
                "monthly_leads": monthly[-6:],
                "funnel": funnel,
                "activity": [
                    {"who": a.lead.full_name, "what": a.details, "type": a.interaction_type, "when": a.created_at}
                    for a in activity
                ],
            }
        )


@extend_schema(
    tags=["Back-office CRM"],
    summary="Recherche globale de l'en-tête : biens, prospects et (administrateurs) utilisateurs",
    parameters=[OpenApiParameter("q", str, description="2 caractères minimum")],
    responses={200: GlobalSearchSchema},
)
class GlobalSearchView(APIView):
    permission_classes = [IsStaffOrAgent]
    LIMIT = 5

    def get(self, request):
        from apps.users.infrastructure.models import User
        from apps.users.interfaces.permissions import is_admin

        q = (request.query_params.get("q") or "").strip()
        out = {"properties": [], "leads": [], "users": []}
        if len(q) < 2:
            return Response(out)

        props = (
            Property.objects.exclude(status=PropertyStatus.ARCHIVE)
            .filter(
                Q(title__icontains=q)
                | Q(reference__icontains=q)
                | Q(neighborhood__icontains=q)
                | Q(commune__icontains=q)
            )
            .order_by("-created_at")[: self.LIMIT]
        )
        out["properties"] = [
            {
                "id": p.id,
                "reference": p.reference,
                "title": p.title,
                "slug": p.slug,
                "commune": p.commune,
                "status_display": p.get_status_display(),
            }
            for p in props
        ]

        leads = Lead.objects.filter(
            Q(full_name__icontains=q) | Q(phone_number__icontains=q) | Q(email__icontains=q)
        ).order_by("-last_interaction_at")[: self.LIMIT]
        out["leads"] = [
            {
                "id": lead.id,
                "full_name": lead.full_name,
                "phone_number": lead.phone_number,
                "stage_display": lead.get_stage_display(),
            }
            for lead in leads
        ]

        if is_admin(request.user):  # la liste des comptes reste réservée aux administrateurs
            users = User.objects.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(phone_number__icontains=q)
            ).order_by("first_name", "last_name")[: self.LIMIT]
            out["users"] = [
                {
                    "id": u.id,
                    "name": f"{u.first_name} {u.last_name}".strip() or u.email,
                    "email": u.email,
                    "role_display": u.get_role_display(),
                }
                for u in users
            ]
        return Response(out)
