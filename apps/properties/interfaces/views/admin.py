"""Back-office : catalogue complet des biens."""

from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.users.interfaces.permissions import IsStaffOrAgent

from ..serializers import (
    PropertyAdminWriteSerializer,
    PropertyCardSerializer,
    PropertyDetailSerializer,
)
from ._common import apply_search_filters, cards_qs, ctx


@extend_schema(
    tags=["Back-office Catalogue"],
    summary="Tous les biens, quel que soit leur statut (?q, status, verification, commune, type, tour=requested|published)",
)
class AdminPropertyListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsStaffOrAgent]

    def get_serializer_class(self):
        return PropertyAdminWriteSerializer if self.request.method == "POST" else PropertyCardSerializer

    def get_serializer_context(self):
        return ctx(self.request)

    def get_queryset(self):
        params = self.request.query_params
        qs = cards_qs().annotate(leads_count=Count("leads", distinct=True))
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("verification"):
            qs = qs.filter(verification_status=params["verification"])
        tour = params.get("tour")
        if tour == "published":
            qs = qs.exclude(virtual_tour_url__isnull=True).exclude(virtual_tour_url="")
        elif tour == "requested":
            qs = qs.filter(tour_scan_requested=True).filter(Q(virtual_tour_url__isnull=True) | Q(virtual_tour_url=""))
        return apply_search_filters(qs, params)


@extend_schema(tags=["Back-office Catalogue"])
class AdminPropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = cards_qs().select_related("development_project")
    lookup_field = "id"

    def get_serializer_class(self):
        return PropertyDetailSerializer if self.request.method == "GET" else PropertyAdminWriteSerializer

    def get_serializer_context(self):
        return ctx(self.request)
