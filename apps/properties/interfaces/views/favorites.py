"""Favoris de l'acheteur, et vue de l'équipe sur les favoris."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.properties.infrastructure.models import (
    PUBLIC_STATUSES,
    Property,
    PropertyFavorite,
)
from apps.users.interfaces.permissions import IsStaffOrAgent

from ..serializers import (
    FavoriteToggleResponseSerializer,
    PropertyCardSerializer,
    PropertyFavoriteAdminSerializer,
)
from ._common import ctx, public_qs


@extend_schema(tags=["Favoris"])
class FavoritesListView(generics.ListAPIView):
    """Écran 14 : biens favoris de l'utilisateur connecté (encore publiés)."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertyCardSerializer
    pagination_class = None

    def get_queryset(self):
        return public_qs().filter(favorited_by__user=self.request.user)

    def get_serializer_context(self):
        return ctx(self.request)


@extend_schema(tags=["Favoris"], summary="Ajouter ou retirer un bien des favoris", request=None,
               responses={200: FavoriteToggleResponseSerializer, 201: FavoriteToggleResponseSerializer})
class FavoriteToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, property_id):
        prop = get_object_or_404(Property, id=property_id, status__in=PUBLIC_STATUSES)
        fav, created = PropertyFavorite.objects.get_or_create(user=request.user, property=prop)
        if not created:
            fav.delete()
            return Response({'status': 'removed', 'is_favorited': False}, status=status.HTTP_200_OK)
        return Response({'status': 'added', 'is_favorited': True}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Back-office Favoris"])
class AdminPropertyFavoriteListView(generics.ListAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = PropertyFavorite.objects.select_related('property', 'user').order_by('-created_at')
    serializer_class = PropertyFavoriteAdminSerializer


@extend_schema(tags=["Back-office Favoris"], responses={204: None})
class AdminPropertyFavoriteDetailView(generics.DestroyAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = PropertyFavorite.objects.all()
    lookup_field = 'id'
