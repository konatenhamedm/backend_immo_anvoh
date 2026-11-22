from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.interfaces.permissions import IsOwnerRole, IsStaffOrAgent, is_staff_or_agent
from apps.users.interfaces.throttling import ScopedThrottleMixin
from apps.properties.infrastructure.models import Property, PropertyStatus, PUBLIC_STATUSES, TransactionType
from apps.properties.interfaces.serializers import PropertyCardSerializer, favorite_ids_for
from apps.crm.infrastructure.models import (
    Lead, CRMInteraction, PropertyInquiry, VisitRequest, PipelineStage, LeadSource, VisitRequestStatus, SearchAlert,
)
from apps.crm.domain.lead_service import STAGE_ORDER, advance_stage, find_or_create_lead, rescore
from .schemas import AdminDashboardSchema, GlobalSearchSchema, KanbanSchema
from .serializers import (
    PropertyInquiryInputSerializer, PropertyInquiryResponseSerializer, WhatsAppClickTrackSerializer,
    WhatsAppClickTrackResponseSerializer, FindMyPropertyInputSerializer, FindMyPropertyResponseSerializer,
    ScheduleVisitInputSerializer, ScheduleVisitResponseSerializer, MyRequestsResponseSerializer,
    VisitRequestDetailSerializer, VisitUpdateSerializer, PropertyInquiryDetailSerializer, LeadKanbanItemSerializer,
    LeadDetailSerializer, LeadNoteSerializer, CRMInteractionSerializer, SearchAlertSerializer, LeadCreateSerializer,
)

MONTHS_FR = ['Janv.', 'Févr.', 'Mars', 'Avr.', 'Mai', 'Juin', 'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.']
# Correspondance types du questionnaire « Trouver mon bien » → types du catalogue.
TYPE_HINTS = {'villa': 'VILLA', 'duplex': 'DUPLEX', 'terrain': 'TERRAIN', 'immeuble': 'IMMEUBLE', 'maison': 'MAISON',
              'appartement': 'APPARTEMENT', 'f2': 'APPARTEMENT', 'f3': 'APPARTEMENT', 'f4': 'APPARTEMENT', 'meubl': 'RESIDENCE_MEUBLEE'}

# Relations lues par PropertyCardSerializer pour chaque bien : à charger d'un coup (sinon une requête par ligne).
PROPERTY_CARD_RELATED = ('property__owner', 'property__assigned_agent', 'property__accreditation__notary')


def _user(request):
    return request.user if request.user.is_authenticated else None


def _public_property(property_id):
    return get_object_or_404(Property.objects.select_related('assigned_agent'), id=property_id, status__in=PUBLIC_STATUSES)


@extend_schema(tags=["CRM & Écrans"], summary="Écran 08 : Demande d'informations sur un bien",
               request=PropertyInquiryInputSerializer, responses={201: PropertyInquiryResponseSerializer})
class PropertyInquiryView(ScopedThrottleMixin, APIView):
    throttle_scope = 'public_forms'
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PropertyInquiryInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        prop = _public_property(data['property_id'])
        lead = find_or_create_lead(
            phone=data['phone_number'], user=_user(request), full_name=data['full_name'], email=data.get('email', ''),
            source=LeadSource.DEMANDE_INFO, prop=prop, extra={'objective': data['objective'], 'preferred_zone': prop.commune},
        )
        inquiry = PropertyInquiry.objects.create(property=prop, lead=lead, user=_user(request), objective=data['objective'], message=data.get('message', ''))
        CRMInteraction.objects.create(lead=lead, interaction_type="INQUIRY",
                                      details=f"Demande d'info sur {prop.reference} ({prop.title}). Objectif : {data['objective']}")
        rescore(lead)
        lead.save()
        return Response({'message': "Votre demande d'informations a bien été transmise à un conseiller.",
                         'inquiry_id': inquiry.id, 'lead_id': lead.id}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["CRM & Écrans"], summary="Écran 09 : Clic sur le bouton WhatsApp",
               description="Crée ou complète le lead si le visiteur est identifiable (compte ou numéro). Sinon, rien n'est enregistré.",
               request=WhatsAppClickTrackSerializer, responses={200: WhatsAppClickTrackResponseSerializer})
class WhatsAppClickTrackView(ScopedThrottleMixin, APIView):
    throttle_scope = 'public_forms'
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = WhatsAppClickTrackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        prop = Property.objects.filter(id=data['property_id']).first() if data.get('property_id') else None
        lead = find_or_create_lead(phone=data.get('phone_number'), user=_user(request), full_name=data.get('full_name', ''),
                                   source=LeadSource.WHATSAPP, prop=prop)
        if lead is None:
            return Response({'status': 'anonymous', 'lead_id': None})
        CRMInteraction.objects.create(lead=lead, interaction_type="WHATSAPP_CLICK",
                                      details=f"Clic WhatsApp sur {prop.reference} ({prop.title})" if prop else "Clic WhatsApp général")
        rescore(lead)
        lead.save()
        return Response({'status': 'tracked', 'lead_id': lead.id})


@extend_schema(tags=["CRM & Écrans"], summary="Écran 10 : « Trouver mon bien » (questionnaire 7 étapes)",
               request=FindMyPropertyInputSerializer, responses={200: FindMyPropertyResponseSerializer})
class FindMyPropertyView(ScopedThrottleMixin, APIView):
    throttle_scope = 'public_forms'
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = FindMyPropertyInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        is_diaspora = 'diaspora' in data['residence_location'].lower()
        lead = find_or_create_lead(
            phone=data['phone_number'], user=_user(request), full_name=data['full_name'], email=data.get('email', ''),
            source=LeadSource.TROUVER_MON_BIEN,
            extra={
                'objective': data['objective'], 'property_type': data['property_type'], 'preferred_zone': data['preferred_zone'],
                'timeframe': data['timeframe'], 'budget': data.get('budget_amount'),
                'down_payment': data.get('down_payment') or None, 'is_diaspora': is_diaspora,
                'country_of_residence': 'Diaspora' if is_diaspora else "Côte d'Ivoire",
            },
        )
        advance_stage(lead, PipelineStage.QUALIFIE)
        rescore(lead)
        lead.save()
        CRMInteraction.objects.create(lead=lead, interaction_type="QUESTIONNAIRE_7_STEPS",
                                      details=f"Questionnaire : objectif={lead.objective}, zone={lead.preferred_zone}, délai={lead.timeframe}, score={lead.score}")

        recs = Property.objects.filter(status=PropertyStatus.DISPONIBLE).select_related('owner', 'accreditation__notary').prefetch_related('images')
        wanted_type = next((code for hint, code in TYPE_HINTS.items() if hint in data['property_type'].lower()), None)
        for narrowing in (
            {'property_type': wanted_type} if wanted_type else None,
            {'commune__icontains': lead.preferred_zone} if lead.preferred_zone and lead.preferred_zone.lower() != 'autre' else None,
            {'price__lte': lead.budget * Decimal('1.15')} if lead.budget else None,
        ):
            if narrowing and recs.filter(**narrowing).exists():
                recs = recs.filter(**narrowing)
        recommended = list(recs.order_by('-investment_score')[:8])
        return Response({
            'message': f"Nous avons identifié {len(recommended)} opportunités correspondant à votre profil.",
            'lead_id': lead.id, 'score': lead.score, 'temperature': lead.temperature,
            'recommended_properties': PropertyCardSerializer(recommended, many=True, context={'request': request, 'favorite_ids': favorite_ids_for(request)}).data,
        })


@extend_schema(tags=["CRM & Écrans"], summary="Écran 16 : Prise de rendez-vous / visite",
               request=ScheduleVisitInputSerializer, responses={201: ScheduleVisitResponseSerializer})
class ScheduleVisitView(ScopedThrottleMixin, APIView):
    throttle_scope = 'public_forms'
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ScheduleVisitInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        prop = _public_property(data['property_id'])
        lead = find_or_create_lead(phone=data['phone_number'], user=_user(request), full_name=data['full_name'],
                                   email=data.get('email', ''), source=LeadSource.VISITE, prop=prop)
        duplicate = VisitRequest.objects.filter(
            property=prop, lead=lead, scheduled_date=data['scheduled_date'], scheduled_time=data['scheduled_time'],
        ).exclude(status=VisitRequestStatus.ANNULEE).first()
        if duplicate:
            return Response({'message': 'Cette visite est déjà enregistrée.', 'visit_id': duplicate.id, 'lead_id': lead.id})
        visit = VisitRequest.objects.create(
            property=prop, lead=lead, user=_user(request), visit_type=data['visit_type'],
            scheduled_date=data['scheduled_date'], scheduled_time=data['scheduled_time'], notes=data.get('notes', ''),
        )
        advance_stage(lead, PipelineStage.RDV)
        rescore(lead)
        lead.save()
        CRMInteraction.objects.create(lead=lead, interaction_type="VISIT_SCHEDULED",
                                      details=f"Visite {visit.get_visit_type_display()} le {data['scheduled_date']} à {data['scheduled_time']:%H:%M} sur {prop.reference}")
        return Response({'message': "Votre demande de rendez-vous est enregistrée. Le conseiller vous confirme le créneau.",
                         'visit_id': visit.id, 'lead_id': lead.id}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["CRM & Écrans"], summary="Écran 15 : Mes demandes (espace client)", responses={200: MyRequestsResponseSerializer})
class MyRequestsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        c = {'request': request, 'favorite_ids': favorite_ids_for(request)}
        inquiries = PropertyInquiry.objects.filter(user=user).select_related(*PROPERTY_CARD_RELATED, 'lead').prefetch_related('property__images')
        visits = VisitRequest.objects.filter(Q(user=user) | Q(lead__user=user)).select_related(*PROPERTY_CARD_RELATED, 'lead').prefetch_related('property__images').distinct()
        leads = list(Lead.objects.filter(user=user).select_related('assigned_agent'))
        best = max(leads, key=lambda l: STAGE_ORDER.index(l.stage) if l.stage in STAGE_ORDER else -1, default=None)
        return Response({
            'inquiries': PropertyInquiryDetailSerializer(inquiries, many=True, context=c).data,
            'visits': VisitRequestDetailSerializer(visits, many=True, context=c).data,
            'project_status': {
                'stage': best.get_stage_display() if best else 'Recherche en cours',
                'stage_code': best.stage if best else 'RECHERCHE',
                'assigned_agent': (f"{best.assigned_agent.first_name} {best.assigned_agent.last_name}".strip()
                                   if best and best.assigned_agent else 'Conseiller THIEBBRO'),
            },
        })


@extend_schema(tags=["CRM & Écrans"], summary="Annuler une de mes visites", request=None, responses={200: VisitRequestDetailSerializer})
class MyVisitCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        visit = get_object_or_404(VisitRequest.objects.filter(Q(user=request.user) | Q(lead__user=request.user)), id=id)
        if visit.status in (VisitRequestStatus.EFFECTUEE, VisitRequestStatus.ANNULEE):
            return Response({'detail': 'Cette visite ne peut plus être annulée.'}, status=status.HTTP_400_BAD_REQUEST)
        visit.status = VisitRequestStatus.ANNULEE
        visit.save(update_fields=['status'])
        CRMInteraction.objects.create(lead=visit.lead, interaction_type="VISIT_CANCELLED", details=f"Visite du {visit.scheduled_date} annulée par le client")
        return Response(VisitRequestDetailSerializer(visit, context={'request': request}).data)


# ---------------------------------------------------------------------------
# Visites côté propriétaire
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Back-office CRM
# ---------------------------------------------------------------------------

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


@extend_schema(tags=["Back-office CRM"], summary="Rendez-vous & visites (?status, ?type, ?upcoming=1)")
class VisitRequestListAdminView(generics.ListAPIView):
    permission_classes = [IsStaffOrAgent]
    serializer_class = VisitRequestDetailSerializer

    def get_queryset(self):
        params = self.request.query_params
        qs = VisitRequest.objects.select_related(*PROPERTY_CARD_RELATED, 'lead').prefetch_related('property__images')
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        if params.get('type'):
            qs = qs.filter(visit_type=params['type'])
        if params.get('upcoming') in ('1', 'true'):
            qs = qs.filter(scheduled_date__gte=timezone.localdate())
        return qs


@extend_schema(tags=["Back-office CRM"])
class VisitRequestDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = VisitRequest.objects.select_related(*PROPERTY_CARD_RELATED, 'lead')
    lookup_field = 'id'

    def get_serializer_class(self):
        return VisitRequestDetailSerializer if self.request.method == 'GET' else VisitUpdateSerializer


@extend_schema(tags=["Back-office CRM"], summary="Demandes d'informations (?processed=0|1)")
class PropertyInquiryListAdminView(generics.ListAPIView):
    permission_classes = [IsStaffOrAgent]
    serializer_class = PropertyInquiryDetailSerializer

    def get_queryset(self):
        qs = PropertyInquiry.objects.select_related(*PROPERTY_CARD_RELATED, 'lead').prefetch_related('property__images').order_by('-created_at')
        processed = self.request.query_params.get('processed')
        if processed in ('0', '1'):
            qs = qs.filter(is_processed=processed == '1')
        return qs


@extend_schema(tags=["Back-office CRM"], summary="Marquer une demande comme traitée")
class PropertyInquiryDetailAdminView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = PropertyInquiry.objects.select_related(*PROPERTY_CARD_RELATED, 'lead')
    serializer_class = PropertyInquiryDetailSerializer
    lookup_field = 'id'


@extend_schema(tags=["Back-office CRM"], summary="Tableau de bord commercial : portefeuille, prospects, visites, entonnoir, activité",
               responses={200: AdminDashboardSchema})
class AdminDashboardView(APIView):
    permission_classes = [IsStaffOrAgent]

    def get(self, request):
        from apps.accreditation.infrastructure.models import AccreditationFile, AccreditationStatus
        today = timezone.localdate()
        public = Property.objects.filter(status__in=PUBLIC_STATUSES)
        sales = public.filter(transaction=TransactionType.VENTE)
        leads = Lead.objects.all()
        active_leads = leads.exclude(stage__in=[PipelineStage.VENTE, PipelineStage.PERDU])
        week_end = today + timedelta(days=7 - today.weekday())

        start = (today.replace(day=1) - timedelta(days=150)).replace(day=1)
        per_month = {(d.year, d.month): n for d, n in leads.filter(created_at__date__gte=start)
                     .annotate(m=TruncMonth('created_at')).values('m').annotate(n=Count('id')).values_list('m', 'n')}
        monthly, cursor = [], start
        while cursor <= today:
            monthly.append({'month': MONTHS_FR[cursor.month - 1], 'value': per_month.get((cursor.year, cursor.month), 0)})
            cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

        # Entonnoir cumulatif : prospects ayant atteint au moins chaque étape (hors perdus).
        stage_rows = {r['stage']: r for r in leads.exclude(stage=PipelineStage.PERDU).values('stage').annotate(n=Count('id'), budget=Sum('budget'))}
        total = sum(r['n'] for r in stage_rows.values()) or 0
        funnel = []
        for i, stage in enumerate(STAGE_ORDER):
            reached = [stage_rows[s] for s in STAGE_ORDER[i:] if s in stage_rows]
            n = sum(r['n'] for r in reached)
            funnel.append({'stage': stage, 'label': PipelineStage(stage).label, 'count': n,
                           'pct': round(n * 100 / total) if total else 0, 'budget': sum((r['budget'] or 0) for r in reached)})

        activity = CRMInteraction.objects.select_related('lead').order_by('-created_at')[:8]
        return Response({
            'portfolio_value': sales.aggregate(t=Sum('price'))['t'] or 0,
            'properties_for_sale': sales.count(),
            'properties_total': Property.objects.exclude(status='ARCHIVE').count(),
            'active_leads': active_leads.count(),
            'new_leads_this_month': leads.filter(created_at__year=today.year, created_at__month=today.month).count(),
            'visits_this_week': VisitRequest.objects.filter(scheduled_date__gte=today, scheduled_date__lt=week_end)
                                .exclude(status=VisitRequestStatus.ANNULEE).count(),
            'average_yield': round(float(public.exclude(estimated_yield_rate__isnull=True).aggregate(a=Avg('estimated_yield_rate'))['a'] or 0), 2),
            'accreditations_pending': AccreditationFile.objects.filter(status=AccreditationStatus.EN_COURS).count(),
            'monthly_leads': monthly[-6:],
            'funnel': funnel,
            'activity': [{'who': a.lead.full_name, 'what': a.details, 'type': a.interaction_type, 'when': a.created_at} for a in activity],
        })


@extend_schema(tags=["Back-office CRM"], summary="Recherche globale de l'en-tête : biens, prospects et (administrateurs) utilisateurs",
               parameters=[OpenApiParameter('q', str, description="2 caractères minimum")], responses={200: GlobalSearchSchema})
class GlobalSearchView(APIView):
    permission_classes = [IsStaffOrAgent]
    LIMIT = 5

    def get(self, request):
        from apps.users.infrastructure.models import User
        from apps.users.interfaces.permissions import is_admin
        q = (request.query_params.get('q') or '').strip()
        out = {'properties': [], 'leads': [], 'users': []}
        if len(q) < 2:
            return Response(out)

        props = (Property.objects.exclude(status=PropertyStatus.ARCHIVE)
                 .filter(Q(title__icontains=q) | Q(reference__icontains=q) | Q(neighborhood__icontains=q) | Q(commune__icontains=q))
                 .order_by('-created_at')[:self.LIMIT])
        out['properties'] = [{'id': p.id, 'reference': p.reference, 'title': p.title, 'slug': p.slug, 'commune': p.commune,
                              'status_display': p.get_status_display()} for p in props]

        leads = (Lead.objects.filter(Q(full_name__icontains=q) | Q(phone_number__icontains=q) | Q(email__icontains=q))
                 .order_by('-last_interaction_at')[:self.LIMIT])
        out['leads'] = [{'id': l.id, 'full_name': l.full_name, 'phone_number': l.phone_number, 'stage_display': l.get_stage_display()} for l in leads]

        if is_admin(request.user):  # la liste des comptes reste réservée aux administrateurs
            users = (User.objects.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q) | Q(phone_number__icontains=q))
                     .order_by('first_name', 'last_name')[:self.LIMIT])
            out['users'] = [{'id': u.id, 'name': f"{u.first_name} {u.last_name}".strip() or u.email, 'email': u.email,
                             'role_display': u.get_role_display()} for u in users]
        return Response(out)


@extend_schema(tags=["Alertes de recherche"], summary="Mes alertes de recherche")
class SearchAlertListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SearchAlertSerializer
    pagination_class = None

    def get_queryset(self):
        return SearchAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if SearchAlert.objects.filter(user=self.request.user).count() >= 10:
            raise serializers.ValidationError({'detail': '10 alertes maximum par compte.'})
        serializer.save(user=self.request.user)


@extend_schema(tags=["Alertes de recherche"])
class SearchAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SearchAlertSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return SearchAlert.objects.filter(user=self.request.user)


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
