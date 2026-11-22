"""Programmes neufs et lots : lecture ouverte à tous, écriture réservée à l'équipe."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from apps.properties.infrastructure.models import (
    DevelopmentProject,
    ProjectLot,
)
from apps.users.interfaces.permissions import IsStaffOrAgent, ReadOnlyOr

from ..serializers import (
    DevelopmentProjectSerializer,
    ProjectLotSerializer,
)


@extend_schema(tags=["Programmes Neufs"])
class DevelopmentProjectListView(generics.ListCreateAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    queryset = DevelopmentProject.objects.prefetch_related("lots")
    serializer_class = DevelopmentProjectSerializer


@extend_schema(tags=["Programmes Neufs"])
class DevelopmentProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    queryset = DevelopmentProject.objects.prefetch_related("lots")
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
