"""Catalogue public : accueil, recherche, fiche, slugs, référentiels, écran « Investir » (lecture ouverte à tous)."""

from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.properties.infrastructure.models import (
    PUBLIC_STATUSES,
    Property,
    PropertyStatus,
    PropertyType,
    TitleDeedType,
    TransactionType,
)
from apps.users.interfaces.permissions import IsStaffOrAgent, ReadOnlyOr

from ..schemas import CatalogMetaSchema, PropertySlugSchema
from ..serializers import (
    DevelopmentProjectSummarySerializer,
    HomeScreenResponseSerializer,
    InvestmentScreenResponseSerializer,
    PropertyAdminWriteSerializer,
    PropertyCardSerializer,
    PropertyDetailSerializer,
)
from ._common import (
    _visible_or_404,
    apply_search_filters,
    can_manage,
    cards_qs,
    ctx,
    project_summaries,
    public_qs,
)

DEFAULT_COMMUNES = ["Cocody", "Marcory", "Plateau", "Yopougon", "Bingerville", "Grand-Bassam", "Assinie", "Songon"]


@extend_schema(
    tags=["Catalogue & Écrans"],
    summary="Données globales de l'Écran 04 (Accueil)",
    responses={200: HomeScreenResponseSerializer},
)
class HomeScreenView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        active = public_qs().filter(status=PropertyStatus.DISPONIBLE)
        projects = project_summaries()[:4]
        c = ctx(request)
        return Response(
            {
                "featured_opportunities": PropertyCardSerializer(
                    active.filter(is_featured=True)[:6], many=True, context=c
                ).data,
                "recent_properties": PropertyCardSerializer(
                    active.order_by("-created_at")[:8], many=True, context=c
                ).data,
                "development_projects": DevelopmentProjectSummarySerializer(projects, many=True, context=c).data,
                "selected_investments": PropertyCardSerializer(
                    active.filter(is_selected_investment=True)[:6], many=True, context=c
                ).data,
            }
        )


@extend_schema(
    tags=["Catalogue & Écrans"],
    summary="Moteur de recherche (Écrans 05 & 06) — création réservée à l'équipe",
    parameters=[
        OpenApiParameter("q", str),
        OpenApiParameter("commune", str),
        OpenApiParameter("neighborhood", str),
        OpenApiParameter("type", str),
        OpenApiParameter("typology", str),
        OpenApiParameter("target_goal", str),
        OpenApiParameter("transaction", str, description="VENTE | LOCATION"),
        OpenApiParameter("min_price", float),
        OpenApiParameter("max_price", float),
        OpenApiParameter("min_surface", float),
        OpenApiParameter("rooms_count", int),
        OpenApiParameter("min_bedrooms", int),
        OpenApiParameter("verified", bool),
        OpenApiParameter("has_tour", bool),
        OpenApiParameter("ordering", str),
        OpenApiParameter("page_size", int, description="Jusqu'à 100"),
    ],
    responses={200: PropertyCardSerializer(many=True)},
)
class PropertySearchView(generics.ListCreateAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]

    def get_serializer_class(self):
        return PropertyAdminWriteSerializer if self.request.method == "POST" else PropertyCardSerializer

    def get_serializer_context(self):
        return ctx(self.request) if self.request.method == "GET" else super().get_serializer_context()

    def get_queryset(self):
        return apply_search_filters(public_qs(), self.request.query_params)


@extend_schema(
    tags=["Catalogue & Écrans"], summary="Fiche d'un bien par identifiant (modification réservée à l'équipe)"
)
class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    queryset = cards_qs().select_related("development_project")
    lookup_field = "id"

    def get_serializer_class(self):
        return PropertyDetailSerializer if self.request.method == "GET" else PropertyAdminWriteSerializer

    def get_object(self):
        return _visible_or_404(self.request, super().get_object())

    def get_serializer_context(self):
        return ctx(self.request)


@extend_schema(
    tags=["Catalogue & Écrans"],
    summary="Fiche d'un bien par slug (URL du site) — compte une vue",
    responses={200: PropertyDetailSerializer},
)
class PropertyBySlugView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        prop = _visible_or_404(request, get_object_or_404(cards_qs().select_related("development_project"), slug=slug))
        if prop.is_public and not can_manage(request.user, prop) and request.query_params.get("count_view", "1") != "0":
            Property.objects.filter(pk=prop.pk).update(views_count=F("views_count") + 1)
        return Response(PropertyDetailSerializer(prop, context=ctx(request)).data)


@extend_schema(
    tags=["Catalogue & Écrans"],
    summary="Slugs des biens publiés (sitemap, pré-rendu)",
    responses={200: PropertySlugSchema},
)
class PropertySlugListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        rows = Property.objects.filter(status__in=PUBLIC_STATUSES).values("slug", "updated_at")
        return Response(list(rows))


@extend_schema(
    tags=["Catalogue & Écrans"],
    summary="Référentiels : communes, types, transactions, titres",
    responses={200: CatalogMetaSchema},
)
class CatalogMetaView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        used = Property.objects.filter(status__in=PUBLIC_STATUSES).values_list("commune", flat=True).distinct()
        communes = list(dict.fromkeys(DEFAULT_COMMUNES + sorted(c for c in used if c)))
        return Response(
            {
                "communes": communes,
                "property_types": [{"value": v, "label": label} for v, label in PropertyType.choices],
                "transactions": [{"value": v, "label": label} for v, label in TransactionType.choices],
                "title_deeds": [{"value": v, "label": label} for v, label in TitleDeedType.choices],
            }
        )


@extend_schema(
    tags=["Catalogue & Écrans"],
    summary="Données de l'Écran 13 (Espace Investir)",
    responses={200: InvestmentScreenResponseSerializer},
)
class InvestmentScreenView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        active = public_qs().filter(status=PropertyStatus.DISPONIBLE)
        c = ctx(request)
        return Response(
            {
                "top_yield_properties": PropertyCardSerializer(
                    active.exclude(estimated_yield_rate__isnull=True).order_by("-estimated_yield_rate")[:6],
                    many=True,
                    context=c,
                ).data,
                "furnished_residences": PropertyCardSerializer(
                    active.filter(property_type=PropertyType.RESIDENCE_MEUBLEE)[:6], many=True, context=c
                ).data,
                "development_projects": DevelopmentProjectSummarySerializer(
                    project_summaries()[:6], many=True, context=c
                ).data,
                "land_opportunities": PropertyCardSerializer(
                    active.filter(property_type=PropertyType.TERRAIN)[:6], many=True, context=c
                ).data,
            }
        )
