"""Espace propriétaire : visites demandées sur ses biens."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.crm.domain.lead_service import advance_stage
from apps.crm.infrastructure.models import (
    CRMInteraction,
    PipelineStage,
    VisitRequest,
    VisitRequestStatus,
)
from apps.users.interfaces.permissions import IsOwnerRole, is_staff_or_agent

from ..serializers import (
    VisitRequestDetailSerializer,
    VisitUpdateSerializer,
)
from ._common import PROPERTY_CARD_RELATED


@extend_schema(tags=["Espace Propriétaire"], summary="Demandes de visite sur mes biens (?status=)")
class OwnerVisitListView(generics.ListAPIView):
    permission_classes = [IsOwnerRole]
    serializer_class = VisitRequestDetailSerializer
    pagination_class = None

    def get_queryset(self):
        qs = VisitRequest.objects.filter(property__owner=self.request.user).select_related(*PROPERTY_CARD_RELATED, 'lead').prefetch_related('property__images')
        if self.request.query_params.get('status'):
            qs = qs.filter(status=self.request.query_params['status'])
        return qs


@extend_schema(tags=["Espace Propriétaire"], summary="Confirmer, reprogrammer ou refuser une visite", request=VisitUpdateSerializer,
               responses={200: VisitRequestDetailSerializer})
class OwnerVisitUpdateView(APIView):
    permission_classes = [IsOwnerRole]

    def patch(self, request, id):
        qs = VisitRequest.objects.select_related(*PROPERTY_CARD_RELATED, 'lead')
        visit = get_object_or_404(qs if is_staff_or_agent(request.user) else qs.filter(property__owner=request.user), id=id)
        serializer = VisitUpdateSerializer(visit, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        visit = serializer.save()
        if visit.status == VisitRequestStatus.EFFECTUEE:
            advance_stage(visit.lead, PipelineStage.VISITE)
            visit.lead.save()
        CRMInteraction.objects.create(lead=visit.lead, interaction_type="VISIT_UPDATED",
                                      details=f"Visite {visit.get_status_display().lower()} — {visit.scheduled_date} {visit.scheduled_time:%H:%M}")
        return Response(VisitRequestDetailSerializer(visit, context={'request': request}).data)
