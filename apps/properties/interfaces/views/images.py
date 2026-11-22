"""Photos d'un bien : ajout, couverture, suppression (propriétaire du bien ou équipe)."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.properties.infrastructure.models import (
    Property,
    PropertyImage,
)

from ..schemas import ImageCoverSerializer
from ..serializers import (
    ImageUploadSerializer,
    PropertyImageSerializer,
)
from ._common import can_manage


@extend_schema(tags=["Espace Propriétaire"], request=ImageUploadSerializer, responses={201: PropertyImageSerializer},
               summary="Ajouter une photo (fichier multipart ou URL externe)")
class PropertyImageUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, id):
        prop = get_object_or_404(Property, id=id)
        if not can_manage(request.user, prop):
            raise PermissionDenied("Ce bien ne vous appartient pas.")
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        is_cover = d.get('is_cover') or not prop.images.exists()
        if is_cover:
            prop.images.update(is_cover=False)
        img = PropertyImage.objects.create(
            property=prop, image=d.get('image'), external_url=d.get('external_url', ''), caption=d.get('caption', ''),
            is_cover=is_cover, order=prop.images.count(),
        )
        return Response(PropertyImageSerializer(img, context={'request': request}).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Espace Propriétaire"], summary="Supprimer une photo / la mettre en couverture (PATCH is_cover)")
class PropertyImageDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get(self, request, id):
        img = get_object_or_404(PropertyImage.objects.select_related('property'), id=id)
        if not can_manage(request.user, img.property):
            raise PermissionDenied("Ce bien ne vous appartient pas.")
        return img

    @extend_schema(request=ImageCoverSerializer, responses={200: PropertyImageSerializer})
    def patch(self, request, id):
        img = self._get(request, id)
        if request.data.get('is_cover'):
            img.property.images.update(is_cover=False)
            img.is_cover = True
            img.save(update_fields=['is_cover'])
        return Response(PropertyImageSerializer(img, context={'request': request}).data)

    @extend_schema(request=None, responses={204: None})
    def delete(self, request, id):
        self._get(request, id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
