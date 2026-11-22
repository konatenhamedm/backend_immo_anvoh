"""Back-office : prospects (kanban, fiche, notes, création)."""

from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.crm.domain.lead_service import advance_stage, find_or_create_lead, rescore
from apps.crm.infrastructure.models import (
    CRMInteraction,
    Lead,
    PipelineStage,
)
from apps.properties.infrastructure.models import Property
from apps.users.interfaces.permissions import IsStaffOrAgent

from ..schemas import KanbanSchema
from ..serializers import (
    CRMInteractionSerializer,
    LeadCreateSerializer,
    LeadDetailSerializer,
    LeadKanbanItemSerializer,
    LeadNoteSerializer,
)


@extend_schema(tags=["Back-office CRM"], summary="Écran 26 : Pipeline Kanban (?agent=me, 50 leads par colonne)",
               responses={200: KanbanSchema})
class PipelineKanbanView(APIView):
    permission_classes = [IsStaffOrAgent]

    def get(self, request):
        base = Lead.objects.select_related('consulted_property', 'assigned_agent')
        if request.query_params.get('agent') == 'me':
            base = base.filter(assigned_agent=request.user)
        counts = dict(base.values('stage').annotate(n=Count('id')).values_list('stage', 'n'))
        budgets = dict(base.values('stage').annotate(t=Sum('budget')).values_list('stage', 't'))
        kanban = {}
        for key, label in PipelineStage.choices:
            leads = base.filter(stage=key).order_by('-score', '-last_interaction_at')[:50]
            kanban[key] = {'label': label, 'count': counts.get(key, 0), 'budget_total': budgets.get(key) or 0,
                           'leads': LeadKanbanItemSerializer(leads, many=True).data}
        return Response(kanban)


@extend_schema(tags=["Back-office CRM"], summary="Fiche prospect : consulter, changer d'étape, assigner, noter")
class LeadDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = Lead.objects.select_related('consulted_property', 'assigned_agent').prefetch_related(
        'interactions', 'visits__property__images', 'inquiries__property__images')
    lookup_field = 'id'

    def get_serializer_class(self):
        return LeadDetailSerializer if self.request.method == 'GET' else LeadKanbanItemSerializer

    def perform_update(self, serializer):
        before = serializer.instance.stage
        lead = serializer.save()
        if lead.stage != before:
            CRMInteraction.objects.create(lead=lead, interaction_type="STAGE_CHANGE",
                                          details=f"Étape : {PipelineStage(before).label} → {lead.get_stage_display()} (par {self.request.user.first_name or self.request.user.email})")
        rescore(lead)
        lead.save(update_fields=['score', 'temperature', 'last_interaction_at'])


@extend_schema(tags=["Back-office CRM"], summary="Ajouter une note / un appel à l'historique du prospect",
               request=LeadNoteSerializer, responses={201: CRMInteractionSerializer})
class LeadNoteView(APIView):
    permission_classes = [IsStaffOrAgent]

    def post(self, request, id):
        lead = get_object_or_404(Lead, id=id)
        serializer = LeadNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interaction = CRMInteraction.objects.create(lead=lead, **serializer.validated_data)
        lead.save(update_fields=['last_interaction_at'])
        return Response(CRMInteractionSerializer(interaction).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Back-office CRM"], request=LeadCreateSerializer, responses={201: LeadKanbanItemSerializer},
               summary="Ajouter un prospect au pipeline (dédoublonné par téléphone)")
class LeadCreateAdminView(APIView):
    permission_classes = [IsStaffOrAgent]

    def post(self, request):
        serializer = LeadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        prop = Property.objects.filter(id=d['consulted_property']).first() if d.get('consulted_property') else None
        lead = find_or_create_lead(
            phone=d['phone_number'], full_name=d['full_name'], email=d.get('email', ''), source=d['source'], prop=prop,
            extra={'budget': d.get('budget'), 'commercial_notes': d.get('commercial_notes', '')},
        )
        if lead is None:
            return Response({'detail': 'Numéro de téléphone requis.'}, status=status.HTTP_400_BAD_REQUEST)
        if d['assign_to_me']:
            lead.assigned_agent = request.user
        advance_stage(lead, d['stage'])
        rescore(lead)
        lead.save()
        CRMInteraction.objects.create(lead=lead, interaction_type="MANUAL_ENTRY",
                                      details=f"Prospect saisi par {request.user.first_name or request.user.email} ({lead.get_source_display()})")
        return Response(LeadKanbanItemSerializer(lead).data, status=status.HTTP_201_CREATED)
