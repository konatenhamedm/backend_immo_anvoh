"""Espace propriétaire : mes biens, modification, tableau de bord."""

from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.properties.infrastructure.models import (
    PUBLIC_STATUSES,
    Property,
    PropertyStatus,
    VerificationStatus,
)
from apps.users.interfaces.permissions import IsOwnerRole, is_admin

from ..schemas import OwnerDashboardSchema
from ..serializers import (
    PropertyCardSerializer,
    PropertyDetailSerializer,
    PropertyWriteSerializer,
)
from ._common import cards_qs, ctx, owner_qs

MONTHS_FR = ["Janv.", "Févr.", "Mars", "Avr.", "Mai", "Juin", "Juil.", "Août", "Sept.", "Oct.", "Nov.", "Déc."]


# Champs dont la modification relance la vérification notariale d'un bien déjà certifié.
SENSITIVE_FIELDS = ("commune", "neighborhood", "surface_sqm", "property_type", "title_deed")


@extend_schema(tags=["Espace Propriétaire"], summary="Mes biens / publier un bien (part en vérification notariale)")
class OwnerPropertyListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOwnerRole]
    pagination_class = None

    def get_serializer_class(self):
        return PropertyWriteSerializer if self.request.method == "POST" else PropertyCardSerializer

    def get_serializer_context(self):
        return ctx(self.request)

    def get_queryset(self):
        return owner_qs(self.request.user).exclude(status=PropertyStatus.ARCHIVE)

    def create(self, request, *args, **kwargs):
        from apps.accreditation.domain.services import ensure_file

        serializer = PropertyWriteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        draft = request.data.get("draft") in (True, "true", "1")
        prop = serializer.save(
            owner=request.user,
            status=PropertyStatus.BROUILLON if draft else PropertyStatus.EN_ATTENTE,
            verification_status=VerificationStatus.NON_VERIFIE if draft else VerificationStatus.EN_ATTENTE,
            is_featured=False,
            is_selected_investment=False,
        )
        if not draft:
            ensure_file(prop)
        prop = owner_qs(request.user).get(pk=prop.pk)
        return Response(PropertyDetailSerializer(prop, context=ctx(request)).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Espace Propriétaire"], summary="Consulter / modifier / retirer un de mes biens")
class OwnerPropertyDetailView(APIView):
    permission_classes = [IsOwnerRole]

    def _get(self, request, id):
        prop = get_object_or_404(owner_qs(request.user) if not is_admin(request.user) else cards_qs(), id=id)
        return prop

    @extend_schema(responses={200: PropertyDetailSerializer})
    def get(self, request, id):
        return Response(PropertyDetailSerializer(self._get(request, id), context=ctx(request)).data)

    @extend_schema(request=PropertyWriteSerializer, responses={200: PropertyDetailSerializer})
    def patch(self, request, id):
        from apps.accreditation.domain.services import ensure_file
        from apps.accreditation.infrastructure.models import AccreditationStatus, AccreditationStep

        prop = self._get(request, id)
        before = {f: getattr(prop, f) for f in SENSITIVE_FIELDS}
        serializer = PropertyWriteSerializer(prop, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        prop = serializer.save()

        submit = request.data.get("submit") in (True, "true", "1")
        changed = any(getattr(prop, f) != v for f, v in before.items())
        file = getattr(prop, "accreditation", None)  # RelatedObjectDoesNotExist hérite d'AttributeError
        if submit and prop.status == PropertyStatus.BROUILLON:
            ensure_file(prop)  # brouillon soumis (ou correction après refus)
        elif changed and file and file.status == AccreditationStatus.CERTIFIE:
            # Le bien reste en ligne, mais le notaire revérifie le dossier.
            file.status, file.step = AccreditationStatus.EN_COURS, AccreditationStep.CONTROLE_JURIDIQUE
            file.save(update_fields=["status", "step", "updated_at"])
            prop.verification_status = VerificationStatus.EN_ATTENTE
            prop.save(update_fields=["verification_status", "updated_at"])
        return Response(PropertyDetailSerializer(self._get(request, id), context=ctx(request)).data)

    @extend_schema(request=None, responses={204: None}, summary="Retirer un de mes biens (archivage)")
    def delete(self, request, id):
        prop = self._get(request, id)
        if prop.status in (PropertyStatus.RESERVE, PropertyStatus.VENDU):
            return Response(
                {"detail": "Un bien réservé ou vendu ne peut pas être retiré."}, status=status.HTTP_400_BAD_REQUEST
            )
        prop.status = PropertyStatus.ARCHIVE
        prop.save(update_fields=["status", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Espace Propriétaire"],
    summary="Vue d'ensemble : audience, demandes, visites, accréditations",
    responses={200: OwnerDashboardSchema},
)
class OwnerDashboardView(APIView):
    permission_classes = [IsOwnerRole]

    def get(self, request):
        from apps.accreditation.infrastructure.models import AccreditationFile, AccreditationStatus
        from apps.crm.infrastructure.models import Lead, VisitRequest, VisitRequestStatus

        props = Property.objects.filter(owner=request.user).exclude(status=PropertyStatus.ARCHIVE)
        today = timezone.localdate()
        start = (today.replace(day=1) - timedelta(days=150)).replace(day=1)
        leads_by_month = dict(
            Lead.objects.filter(consulted_property__owner=request.user, created_at__date__gte=start)
            .annotate(m=TruncMonth("created_at"))
            .values("m")
            .annotate(n=Count("id"))
            .values_list("m", "n")
        )
        months, cursor = [], start
        while cursor <= today:
            key = next((k for k in leads_by_month if k.year == cursor.year and k.month == cursor.month), None)
            months.append({"month": MONTHS_FR[cursor.month - 1], "value": leads_by_month.get(key, 0) if key else 0})
            cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
        return Response(
            {
                "properties_total": props.count(),
                "properties_online": props.filter(status__in=PUBLIC_STATUSES).count(),
                "views_total": sum(props.values_list("views_count", flat=True)),
                "leads_total": Lead.objects.filter(consulted_property__owner=request.user).count(),
                "visits_pending": VisitRequest.objects.filter(
                    property__owner=request.user, status=VisitRequestStatus.EN_ATTENTE
                ).count(),
                "visits_upcoming": VisitRequest.objects.filter(
                    property__owner=request.user, status=VisitRequestStatus.CONFIRMEE, scheduled_date__gte=today
                ).count(),
                "accreditations_in_progress": AccreditationFile.objects.filter(
                    property__owner=request.user, status=AccreditationStatus.EN_COURS
                ).count(),
                "monthly_leads": months[-6:],
            }
        )
