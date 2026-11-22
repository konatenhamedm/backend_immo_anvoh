"""Back-office : rendez-vous / visites et demandes d'informations."""

from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.crm.infrastructure.models import (
    PropertyInquiry,
    VisitRequest,
)
from apps.users.interfaces.permissions import IsStaffOrAgent

from ..serializers import (
    PropertyInquiryDetailSerializer,
    VisitRequestDetailSerializer,
    VisitUpdateSerializer,
)
from ._common import PROPERTY_CARD_RELATED


@extend_schema(tags=["Back-office CRM"], summary="Rendez-vous & visites (?status, ?type, ?upcoming=1)")
class VisitRequestListAdminView(generics.ListAPIView):
    permission_classes = [IsStaffOrAgent]
    serializer_class = VisitRequestDetailSerializer

    def get_queryset(self):
        params = self.request.query_params
        qs = VisitRequest.objects.select_related(*PROPERTY_CARD_RELATED, "lead").prefetch_related("property__images")
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("type"):
            qs = qs.filter(visit_type=params["type"])
        if params.get("upcoming") in ("1", "true"):
            qs = qs.filter(scheduled_date__gte=timezone.localdate())
        return qs


@extend_schema(tags=["Back-office CRM"])
class VisitRequestDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = VisitRequest.objects.select_related(*PROPERTY_CARD_RELATED, "lead")
    lookup_field = "id"

    def get_serializer_class(self):
        return VisitRequestDetailSerializer if self.request.method == "GET" else VisitUpdateSerializer


@extend_schema(tags=["Back-office CRM"], summary="Demandes d'informations (?processed=0|1)")
class PropertyInquiryListAdminView(generics.ListAPIView):
    permission_classes = [IsStaffOrAgent]
    serializer_class = PropertyInquiryDetailSerializer

    def get_queryset(self):
        qs = (
            PropertyInquiry.objects.select_related(*PROPERTY_CARD_RELATED, "lead")
            .prefetch_related("property__images")
            .order_by("-created_at")
        )
        processed = self.request.query_params.get("processed")
        if processed in ("0", "1"):
            qs = qs.filter(is_processed=processed == "1")
        return qs


@extend_schema(tags=["Back-office CRM"], summary="Marquer une demande comme traitée")
class PropertyInquiryDetailAdminView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = PropertyInquiry.objects.select_related(*PROPERTY_CARD_RELATED, "lead")
    serializer_class = PropertyInquiryDetailSerializer
    lookup_field = "id"
