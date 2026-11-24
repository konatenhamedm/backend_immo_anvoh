"""Programmes neufs et lots : lecture ouverte à tous, écriture réservée à l'équipe."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.properties.infrastructure.models import (
    DevelopmentProject,
    ProjectDocument,
    ProjectLot,
)
from apps.users.interfaces.permissions import IsStaffOrAgent, ReadOnlyOr

from ..serializers import (
    DevelopmentProjectSerializer,
    ProjectDocumentSerializer,
    ProjectDocumentUploadSerializer,
    DevelopmentProjectSummarySerializer,
    ProjectLotSerializer,
)
from ._common import project_summaries


@extend_schema(tags=["Programmes Neufs"])
class DevelopmentProjectListView(generics.ListCreateAPIView):
    """Liste des programmes. `?summary=1` : version allégée (décomptes de lots, sans la liste des lots) pour le site."""

    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]

    def _summary(self) -> bool:
        return self.request.method == "GET" and self.request.query_params.get("summary") in ("1", "true")

    def get_queryset(self):
        if self._summary():
            return project_summaries().order_by("-is_featured", "-created_at")
        return DevelopmentProject.objects.prefetch_related("lots", "documents")

    def get_serializer_class(self):
        return DevelopmentProjectSummarySerializer if self._summary() else DevelopmentProjectSerializer


@extend_schema(tags=["Programmes Neufs"], summary="Fiche d'un programme par son slug (lecture seule, avec ses lots)")
class DevelopmentProjectBySlugView(generics.RetrieveAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    queryset = DevelopmentProject.objects.prefetch_related("lots", "documents")
    serializer_class = DevelopmentProjectSerializer
    lookup_field = "slug"


@extend_schema(tags=["Programmes Neufs"])
class DevelopmentProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    queryset = DevelopmentProject.objects.prefetch_related("lots", "documents")
    serializer_class = DevelopmentProjectSerializer
    lookup_field = "id"


@extend_schema(tags=["Programmes Neufs"])
class ProjectLotListCreateView(generics.ListCreateAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    serializer_class = ProjectLotSerializer
    pagination_class = None

    def get_queryset(self):
        return ProjectLot.objects.filter(project_id=self.kwargs.get("project_id"))

    def perform_create(self, serializer):
        serializer.save(project=get_object_or_404(DevelopmentProject, id=self.kwargs.get("project_id")))


@extend_schema(tags=["Programmes Neufs"])
class ProjectLotDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    queryset = ProjectLot.objects.all()
    serializer_class = ProjectLotSerializer
    lookup_field = "id"


@extend_schema(
    tags=["Programmes Neufs"],
    summary="Ajouter un plan ou un document à un programme (équipe) : PDF, JPG, PNG ou WebP, 20 Mo au plus",
    request={"multipart/form-data": ProjectDocumentUploadSerializer},
    responses={201: ProjectDocumentSerializer},
)
class ProjectDocumentCreateView(generics.GenericAPIView):
    permission_classes = [IsStaffOrAgent]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = ProjectDocumentUploadSerializer

    def post(self, request, project_id):
        project = get_object_or_404(DevelopmentProject, id=project_id)
        s = ProjectDocumentUploadSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        doc = ProjectDocument.objects.create(project=project, **s.validated_data)
        return Response(ProjectDocumentSerializer(doc, context={"request": request}).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Programmes Neufs"], summary="Retirer un plan ou un document (équipe)")
class ProjectDocumentDeleteView(generics.DestroyAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = ProjectDocument.objects.all()
    lookup_field = "id"
