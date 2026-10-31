from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, serializers, generics
from drf_spectacular.utils import extend_schema
from decimal import Decimal

from apps.properties.infrastructure.models import Property, PropertyStatus
from apps.properties.interfaces.serializers import PropertyCardSerializer
from apps.crm.infrastructure.models import (
    Lead, CRMInteraction, PropertyInquiry, VisitRequest,
    PipelineStage, LeadSource, VisitRequestStatus
)
from apps.crm.domain.scoring_service import LeadScoringDomainService
from .serializers import (
    PropertyInquiryInputSerializer,
    PropertyInquiryResponseSerializer,
    WhatsAppClickTrackSerializer,
    WhatsAppClickTrackResponseSerializer,
    FindMyPropertyInputSerializer,
    FindMyPropertyResponseSerializer,
    ScheduleVisitInputSerializer,
    ScheduleVisitResponseSerializer,
    MyRequestsResponseSerializer,
    VisitRequestDetailSerializer,
    PropertyInquiryDetailSerializer,
    LeadKanbanItemSerializer
)

@extend_schema(
    tags=["CRM & Écrans"],
    summary="Écran 08 : Demande d'informations sur un bien",
    description="Crée automatiquement le lead, l'associe au bien et loggue l'interaction commerciale.",
    request=PropertyInquiryInputSerializer,
    responses={201: PropertyInquiryResponseSerializer}
)
class PropertyInquiryView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PropertyInquiryInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            prop = Property.objects.get(id=data['property_id'])
        except Property.DoesNotExist:
            return Response({'detail': 'Bien introuvable'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user if request.user.is_authenticated else None

        # Recherche ou création du lead
        lead, _ = Lead.objects.get_or_create(
            phone_number=data['phone_number'],
            defaults={
                'full_name': data['full_name'],
                'email': data.get('email', ''),
                'user': user,
                'source': LeadSource.DEMANDE_INFO,
                'consulted_property': prop,
                'objective': data['objective'],
                'preferred_zone': prop.commune,
                'assigned_agent': prop.assigned_agent
            }
        )

        # Calcul automatique du score
        score, temp = LeadScoringDomainService.calculate_score(
            has_confirmed_budget=bool(lead.budget),
            has_confirmed_down_payment=bool(lead.down_payment),
            timeframe_under_3_months=False,
            has_identified_property=True,
            has_visit_request=False
        )
        lead.score = score
        lead.temperature = temp
        lead.consulted_property = prop
        lead.save()

        # Création de l'inquiry
        inquiry = PropertyInquiry.objects.create(
            property=prop,
            lead=lead,
            user=user,
            objective=data['objective'],
            message=data.get('message', '')
        )

        # Log de l'interaction
        CRMInteraction.objects.create(
            lead=lead,
            interaction_type="INQUIRY",
            details=f"Demande d'info sur le bien {prop.reference} ({prop.title}). Objectif: {data['objective']}"
        )

        return Response({
            'message': 'Votre demande d\'informations a bien été transmise à un conseiller.',
            'inquiry_id': inquiry.id,
            'lead_id': lead.id
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["CRM & Écrans"],
    summary="Écran 09 : Enregistrer le clic sur le bouton WhatsApp",
    description="Loggue le clic WhatsApp dans le CRM comme opportunité / interaction commerciale.",
    request=WhatsAppClickTrackSerializer,
    responses={200: WhatsAppClickTrackResponseSerializer}
)
class WhatsAppClickTrackView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = WhatsAppClickTrackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        prop = None
        if data.get('property_id'):
            prop = Property.objects.filter(id=data['property_id']).first()

        phone = data.get('phone_number') or (request.user.phone_number if request.user.is_authenticated else 'Inconnu')
        full_name = data.get('full_name') or (f"{request.user.first_name} {request.user.last_name}" if request.user.is_authenticated else 'Visiteur WhatsApp')

        lead, _ = Lead.objects.get_or_create(
            phone_number=phone,
            defaults={
                'full_name': full_name,
                'source': LeadSource.WHATSAPP,
                'consulted_property': prop,
                'assigned_agent': prop.assigned_agent if prop else None
            }
        )

        details = f"Clic sur bouton WhatsApp pour le bien {prop.reference} ({prop.title})" if prop else "Clic sur bouton WhatsApp général"
        CRMInteraction.objects.create(
            lead=lead,
            interaction_type="WHATSAPP_CLICK",
            details=details
        )

        return Response({'status': 'tracked', 'lead_id': lead.id}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["CRM & Écrans"],
    summary="Écran 10 : Formulaire 'Trouver mon bien' (Questionnaire 7 étapes)",
    description="Enregistre le profil du prospect, calcule son score automatique et retourne jusqu'à 8 biens recommandés.",
    request=FindMyPropertyInputSerializer,
    responses={200: FindMyPropertyResponseSerializer}
)
class FindMyPropertyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = FindMyPropertyInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user if request.user.is_authenticated else None
        is_diaspora = 'diaspora' in data['residence_location'].lower()

        lead, _ = Lead.objects.get_or_create(
            phone_number=data['phone_number'],
            defaults={
                'full_name': data['full_name'],
                'email': data.get('email', ''),
                'user': user,
                'source': LeadSource.TROUVER_MON_BIEN,
                'country_of_residence': 'Diaspora' if is_diaspora else 'Côte d\'Ivoire',
                'is_diaspora': is_diaspora,
            }
        )

        lead.objective = data['objective']
        lead.property_type = data['property_type']
        lead.preferred_zone = data['preferred_zone']
        lead.timeframe = data['timeframe']
        if data.get('budget_amount'):
            lead.budget = data['budget_amount']
        if data.get('down_payment'):
            lead.down_payment = data['down_payment']

        # Scoring automatique (Écran 27)
        timeframe_under_3_months = any(w in data['timeframe'].lower() for w in ['immédiat', '0-3', '0 à 3'])
        score, temp = LeadScoringDomainService.calculate_score(
            has_confirmed_budget=bool(lead.budget),
            has_confirmed_down_payment=bool(lead.down_payment and lead.down_payment > 0),
            timeframe_under_3_months=timeframe_under_3_months,
            has_identified_property=False,
            has_visit_request=False
        )
        lead.score = score
        lead.temperature = temp
        lead.save()

        # Log interaction
        CRMInteraction.objects.create(
            lead=lead,
            interaction_type="QUESTIONNAIRE_7_STEPS",
            details=f"Questionnaire complété: Objectif={lead.objective}, Zone={lead.preferred_zone}, Délai={lead.timeframe}, Score={score}"
        )

        # Recherche des biens recommandés
        recs_qs = Property.objects.filter(status=PropertyStatus.DISPONIBLE).prefetch_related('images', 'favorited_by')
        if lead.preferred_zone and lead.preferred_zone.lower() != 'autre':
            zone_qs = recs_qs.filter(commune__icontains=lead.preferred_zone)
            if zone_qs.exists():
                recs_qs = zone_qs
        if lead.budget:
            budget_qs = recs_qs.filter(price__lte=lead.budget * Decimal('1.15'))
            if budget_qs.exists():
                recs_qs = budget_qs

        recommended = recs_qs[:8]

        response_data = {
            'message': f"Nous avons identifié {recommended.count()} opportunités correspondant à votre profil.",
            'lead_id': lead.id,
            'score': score,
            'temperature': temp,
            'recommended_properties': PropertyCardSerializer(recommended, many=True, context={'request': request}).data
        }
        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["CRM & Écrans"],
    summary="Écran 16 : Prise de rendez-vous / Visite",
    description="Programme une visite physique ou visio. Notifie le conseiller et met à jour le scoring.",
    request=ScheduleVisitInputSerializer,
    responses={201: ScheduleVisitResponseSerializer}
)
class ScheduleVisitView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ScheduleVisitInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            prop = Property.objects.get(id=data['property_id'])
        except Property.DoesNotExist:
            return Response({'detail': 'Bien introuvable'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user if request.user.is_authenticated else None

        lead, _ = Lead.objects.get_or_create(
            phone_number=data['phone_number'],
            defaults={
                'full_name': data['full_name'],
                'email': data.get('email', ''),
                'user': user,
                'source': LeadSource.VISITE,
                'consulted_property': prop,
                'assigned_agent': prop.assigned_agent
            }
        )

        visit = VisitRequest.objects.create(
            property=prop,
            lead=lead,
            user=user,
            visit_type=data['visit_type'],
            scheduled_date=data['scheduled_date'],
            scheduled_time=data['scheduled_time'],
            notes=data.get('notes', '')
        )

        # Mise à jour étape Kanban CRM : passage en RDV / Visite
        lead.stage = PipelineStage.RDV
        lead.consulted_property = prop
        score, temp = LeadScoringDomainService.calculate_score(
            has_confirmed_budget=bool(lead.budget),
            has_confirmed_down_payment=bool(lead.down_payment),
            timeframe_under_3_months=True,
            has_identified_property=True,
            has_visit_request=True
        )
        lead.score = score
        lead.temperature = temp
        lead.save()

        CRMInteraction.objects.create(
            lead=lead,
            interaction_type="VISIT_SCHEDULED",
            details=f"Visite {data['visit_type']} programmée pour le {data['scheduled_date']} à {data['scheduled_time']} sur {prop.reference}"
        )

        return Response({
            'message': 'Votre demande de rendez-vous a bien été enregistrée. Le conseiller reçoit immédiatement l\'information.',
            'visit_id': visit.id,
            'lead_id': lead.id
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["CRM & Écrans"],
    summary="Écran 15 : Mes Demandes (Espace Client)",
    description="Affiche l'état des demandes d'informations, visites et avancement de projet de l'utilisateur connecté.",
    responses={200: MyRequestsResponseSerializer}
)
class MyRequestsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        inquiries = PropertyInquiry.objects.filter(user=user).select_related('property')
        visits = VisitRequest.objects.filter(user=user).select_related('property')

        # Statut du projet global
        user_lead = Lead.objects.filter(user=user).first()
        project_status = {
            'stage': user_lead.get_stage_display() if user_lead else 'Recherche en cours',
            'stage_code': user_lead.stage if user_lead else 'RECHERCHE',
            'assigned_agent': str(user_lead.assigned_agent) if user_lead and user_lead.assigned_agent else 'Conseiller THIEBBRO',
        }

        data = {
            'inquiries': PropertyInquiryDetailSerializer(inquiries, many=True, context={'request': request}).data,
            'visits': VisitRequestDetailSerializer(visits, many=True, context={'request': request}).data,
            'project_status': project_status
        }
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Back-office CRM"],
    summary="Écran 26 : Pipeline Kanban des Prospects",
    description="Retourne les prospects regroupés par colonne Kanban pour le tableau de bord commercial.",
    responses={200: serializers.DictField()}
)
class PipelineKanbanView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        kanban = {}
        for stage_key, stage_label in PipelineStage.choices:
            leads = Lead.objects.filter(stage=stage_key).select_related('consulted_property')
            kanban[stage_key] = {
                'label': stage_label,
                'count': leads.count(),
                'leads': LeadKanbanItemSerializer(leads, many=True).data
            }
        return Response(kanban, status=status.HTTP_200_OK)


@extend_schema(tags=["Back-office CRM"])
class LeadDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Lead.objects.all().select_related('consulted_property')
    serializer_class = LeadKanbanItemSerializer
    lookup_field = 'id'


@extend_schema(tags=["Back-office CRM"])
class VisitRequestListAdminView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = VisitRequest.objects.all().select_related('property', 'lead')
    serializer_class = VisitRequestDetailSerializer


@extend_schema(tags=["Back-office CRM"])
class VisitRequestDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = VisitRequest.objects.all()
    serializer_class = VisitRequestDetailSerializer
    lookup_field = 'id'


@extend_schema(tags=["Back-office CRM"])
class PropertyInquiryListAdminView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = PropertyInquiry.objects.all().select_related('property', 'lead').order_by('-created_at')
    serializer_class = PropertyInquiryDetailSerializer

