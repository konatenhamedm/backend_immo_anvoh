from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accreditation.domain import services
from apps.accreditation.infrastructure.models import AccreditationFile, Notary, PropertyDocument
from apps.properties.infrastructure.models import Property
from apps.users.interfaces.permissions import (
    IsAdminRole,
    IsNotaryOrAdmin,
    IsOwnerRole,
    IsStaffOrAgent,
    is_admin,
    is_notary,
    is_staff_or_agent,
)

from .serializers import (
    AccreditationActionSerializer,
    AccreditationFileSerializer,
    DocumentReviewSerializer,
    DocumentUploadSerializer,
    NotaryPublicSerializer,
    NotarySerializer,
    PropertyDocumentSerializer,
)


def _files_qs():
    return AccreditationFile.objects.select_related("property__owner", "notary").prefetch_related(
        "property__images", "property__documents"
    )


def _notaries_qs():
    return Notary.objects.annotate(files_count=Count("files", filter=Q(files__status="CERTIFIE")))


@extend_schema(tags=["Accréditation"], summary="Notaires partenaires (public)")
class NotaryPublicListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = NotaryPublicSerializer
    pagination_class = None

    def get_queryset(self):
        return _notaries_qs().filter(is_active=True)


@extend_schema(tags=["Back-office Accréditation"])
class NotaryAdminListCreateView(generics.ListCreateAPIView):
    """Lecture pour toute l'équipe (assignation des dossiers), création réservée aux administrateurs."""

    permission_classes = [IsStaffOrAgent]

    def get_permissions(self):
        return [IsAdminRole()] if self.request.method == "POST" else super().get_permissions()

    serializer_class = NotarySerializer
    pagination_class = None

    def get_queryset(self):
        return _notaries_qs()


@extend_schema(tags=["Back-office Accréditation"])
class NotaryAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = NotarySerializer
    lookup_field = "id"

    def get_queryset(self):
        return _notaries_qs()


@extend_schema(tags=["Accréditation"], summary="Mes dossiers d'accréditation (propriétaire)")
class OwnerAccreditationListView(generics.ListAPIView):
    permission_classes = [IsOwnerRole]
    serializer_class = AccreditationFileSerializer
    pagination_class = None

    def get_queryset(self):
        return _files_qs().filter(property__owner=self.request.user)


@extend_schema(
    tags=["Accréditation"],
    summary="Déposer une pièce justificative",
    request=DocumentUploadSerializer,
    responses={201: PropertyDocumentSerializer},
)
class OwnerDocumentUploadView(APIView):
    permission_classes = [IsOwnerRole]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, property_id):
        prop = get_object_or_404(Property, id=property_id)
        if prop.owner_id != request.user.id and not is_admin(request.user):
            return Response({"detail": "Ce bien ne vous appartient pas."}, status=status.HTTP_403_FORBIDDEN)
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Une seule pièce active par type : la nouvelle remplace l'ancienne.
        PropertyDocument.objects.filter(property=prop, doc_type=serializer.validated_data["doc_type"]).delete()
        doc = PropertyDocument.objects.create(property=prop, **serializer.validated_data)
        services.ensure_file(prop)
        return Response(
            PropertyDocumentSerializer(doc, context={"request": request}).data, status=status.HTTP_201_CREATED
        )


@extend_schema(tags=["Accréditation"], responses={204: None})
class OwnerDocumentDeleteView(generics.DestroyAPIView):
    permission_classes = [IsOwnerRole]
    lookup_field = "id"

    def get_queryset(self):
        qs = PropertyDocument.objects.all()
        return qs if is_admin(self.request.user) else qs.filter(property__owner=self.request.user)


@extend_schema(tags=["Back-office Accréditation"], summary="File de vérification (?status=EN_COURS|CERTIFIE|REFUSE)")
class AccreditationQueueView(generics.ListAPIView):
    """Équipe : tous les dossiers. Notaire : uniquement les dossiers qui lui sont assignés."""

    permission_classes = [IsNotaryOrAdmin]
    serializer_class = AccreditationFileSerializer
    pagination_class = None

    def get_queryset(self):
        qs = _files_qs()
        user = self.request.user
        if is_notary(user) and not is_staff_or_agent(user):
            qs = qs.filter(notary__user=user)
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs


@extend_schema(
    tags=["Back-office Accréditation"],
    request=AccreditationActionSerializer,
    responses={200: AccreditationFileSerializer},
    summary="Faire avancer un dossier : assign | advance | certify | refuse",
)
class AccreditationActionView(APIView):
    permission_classes = [IsNotaryOrAdmin]

    def get(self, request, id):
        return Response(AccreditationFileSerializer(self._get(request, id), context={"request": request}).data)

    def post(self, request, id):
        file = self._get(request, id)
        serializer = AccreditationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            if data["action"] == "assign":
                if not is_staff_or_agent(request.user):
                    return Response(
                        {"detail": "Seule l'équipe Thiebbro assigne les notaires."}, status=status.HTTP_403_FORBIDDEN
                    )
                file.notary = get_object_or_404(Notary, id=data.get("notary_id"), is_active=True)
                file.save(update_fields=["notary", "updated_at"])
            elif data["action"] == "advance":
                services.advance(file)
            elif data["action"] == "certify":
                services.certify(file, data["level"])
            elif data["action"] == "refuse":
                services.refuse(file, data["reason"])
        except services.AccreditationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AccreditationFileSerializer(_files_qs().get(id=file.id), context={"request": request}).data)

    def _get(self, request, id):
        file = get_object_or_404(_files_qs(), id=id)
        if (
            is_notary(request.user)
            and not is_staff_or_agent(request.user)
            and (not file.notary or file.notary.user_id != request.user.id)
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Ce dossier ne vous est pas assigné.")
        return file


@extend_schema(tags=["Back-office Accréditation"], summary="Valider ou rejeter une pièce")
class DocumentReviewView(generics.UpdateAPIView):
    permission_classes = [IsNotaryOrAdmin]
    serializer_class = DocumentReviewSerializer
    lookup_field = "id"
    http_method_names = ["patch"]

    def get_queryset(self):
        qs = PropertyDocument.objects.all()
        user = self.request.user
        if is_notary(user) and not is_staff_or_agent(user):
            qs = qs.filter(property__accreditation__notary__user=user)
        return qs
