"""Espace de l'utilisateur connecté : ses demandes, ses visites, ses alertes de recherche."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.crm.domain.lead_service import STAGE_ORDER
from apps.crm.infrastructure.models import (
    CRMInteraction,
    Lead,
    PropertyInquiry,
    SearchAlert,
    VisitRequest,
    VisitRequestStatus,
)
from apps.properties.interfaces.serializers import favorite_ids_for

from ..serializers import (
    MyRequestsResponseSerializer,
    PropertyInquiryDetailSerializer,
    SearchAlertSerializer,
    VisitRequestDetailSerializer,
)
from ._common import PROPERTY_CARD_RELATED


@extend_schema(
    tags=["CRM & Écrans"],
    summary="Écran 15 : Mes demandes (espace client)",
    responses={200: MyRequestsResponseSerializer},
)
class MyRequestsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        c = {"request": request, "favorite_ids": favorite_ids_for(request)}
        inquiries = (
            PropertyInquiry.objects.filter(user=user)
            .select_related(*PROPERTY_CARD_RELATED, "lead")
            .prefetch_related("property__images")
        )
        visits = (
            VisitRequest.objects.filter(Q(user=user) | Q(lead__user=user))
            .select_related(*PROPERTY_CARD_RELATED, "lead")
            .prefetch_related("property__images")
            .distinct()
        )
        leads = list(Lead.objects.filter(user=user).select_related("assigned_agent"))
        best = max(
            leads, key=lambda lead: STAGE_ORDER.index(lead.stage) if lead.stage in STAGE_ORDER else -1, default=None
        )
        return Response(
            {
                "inquiries": PropertyInquiryDetailSerializer(inquiries, many=True, context=c).data,
                "visits": VisitRequestDetailSerializer(visits, many=True, context=c).data,
                "project_status": {
                    "stage": best.get_stage_display() if best else "Recherche en cours",
                    "stage_code": best.stage if best else "RECHERCHE",
                    "assigned_agent": (
                        f"{best.assigned_agent.first_name} {best.assigned_agent.last_name}".strip()
                        if best and best.assigned_agent
                        else "Conseiller THIEBBRO"
                    ),
                },
            }
        )


@extend_schema(
    tags=["CRM & Écrans"],
    summary="Annuler une de mes visites",
    request=None,
    responses={200: VisitRequestDetailSerializer},
)
class MyVisitCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        visit = get_object_or_404(VisitRequest.objects.filter(Q(user=request.user) | Q(lead__user=request.user)), id=id)
        if visit.status in (VisitRequestStatus.EFFECTUEE, VisitRequestStatus.ANNULEE):
            return Response({"detail": "Cette visite ne peut plus être annulée."}, status=status.HTTP_400_BAD_REQUEST)
        visit.status = VisitRequestStatus.ANNULEE
        visit.save(update_fields=["status"])
        CRMInteraction.objects.create(
            lead=visit.lead,
            interaction_type="VISIT_CANCELLED",
            details=f"Visite du {visit.scheduled_date} annulée par le client",
        )
        return Response(VisitRequestDetailSerializer(visit, context={"request": request}).data)


@extend_schema(tags=["Alertes de recherche"], summary="Mes alertes de recherche")
class SearchAlertListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SearchAlertSerializer
    pagination_class = None

    def get_queryset(self):
        return SearchAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if SearchAlert.objects.filter(user=self.request.user).count() >= 10:
            raise serializers.ValidationError({"detail": "10 alertes maximum par compte."})
        serializer.save(user=self.request.user)


@extend_schema(tags=["Alertes de recherche"])
class SearchAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SearchAlertSerializer
    lookup_field = "id"

    def get_queryset(self):
        return SearchAlert.objects.filter(user=self.request.user)
