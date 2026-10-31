from rest_framework import serializers
from decimal import Decimal
from apps.crm.infrastructure.models import (
    Lead, CRMInteraction, PropertyInquiry, VisitRequest,
    PipelineStage, LeadSource, VisitRequestType, VisitRequestStatus
)
from apps.properties.interfaces.serializers import PropertyCardSerializer

class PropertyInquiryInputSerializer(serializers.Serializer):
    """Écran 08 : Formulaire de demande d'informations sur une fiche bien."""
    property_id = serializers.UUIDField()
    full_name = serializers.CharField(max_length=200)
    phone_number = serializers.CharField(max_length=30)
    email = serializers.EmailField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    objective = serializers.ChoiceField(
        choices=['Habiter', 'Investir', 'Louer', 'Autre'],
        default='Habiter'
    )


class PropertyInquiryResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    inquiry_id = serializers.UUIDField()
    lead_id = serializers.UUIDField()


class WhatsAppClickTrackSerializer(serializers.Serializer):
    """Écran 09 : Enregistrement du clic WhatsApp."""
    property_id = serializers.UUIDField(required=False)
    phone_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    full_name = serializers.CharField(max_length=200, required=False, allow_blank=True)


class WhatsAppClickTrackResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    lead_id = serializers.UUIDField()


class ScheduleVisitResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    visit_id = serializers.UUIDField()
    lead_id = serializers.UUIDField()


class FindMyPropertyInputSerializer(serializers.Serializer):
    """
    Écran 10 : Formulaire "Trouver mon bien" (Questionnaire en 7 étapes).
    Étape 1 : Objectif (Habiter, Investir, Louer)
    Étape 2 : Type de bien (F2, F3, F4, F5, Villa, Terrain, Immeuble)
    Étape 3 : Zone (Cocody, Riviera, Abatta, Bingerville, Marcory, Bassam, Autre)
    Étape 4 : Budget (ex: 50-80 M, 80-120 M, 120-200 M, 200 M+)
    Étape 5 : Apport (montant en FCFA)
    Étape 6 : Délai (Immédiatement, 0-3 mois, 3-6 mois, 6-12 mois, Plus tard)
    Étape 7 : Pays de résidence (Côte d'Ivoire, Diaspora)
    + Coordonnées contact (Nom, Téléphone, Email)
    """
    full_name = serializers.CharField(max_length=200)
    phone_number = serializers.CharField(max_length=30)
    email = serializers.EmailField(required=False, allow_blank=True)
    
    objective = serializers.CharField(max_length=100) # Étape 1
    property_type = serializers.CharField(max_length=100) # Étape 2
    preferred_zone = serializers.CharField(max_length=150) # Étape 3
    budget_range = serializers.CharField(max_length=100) # Étape 4 (ex: "50-80 M")
    budget_amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    down_payment = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=Decimal('0')) # Étape 5
    timeframe = serializers.CharField(max_length=100) # Étape 6
    residence_location = serializers.CharField(max_length=100) # Étape 7 ("Côte d'Ivoire" ou "Diaspora")


class FindMyPropertyResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    lead_id = serializers.UUIDField()
    score = serializers.IntegerField()
    temperature = serializers.CharField()
    recommended_properties = PropertyCardSerializer(many=True)


class ScheduleVisitInputSerializer(serializers.Serializer):
    """Écran 16 : Prise de rendez-vous / Visite."""
    property_id = serializers.UUIDField()
    full_name = serializers.CharField(max_length=200)
    phone_number = serializers.CharField(max_length=30)
    email = serializers.EmailField(required=False, allow_blank=True)
    visit_type = serializers.ChoiceField(choices=VisitRequestType.choices, default=VisitRequestType.PHYSIQUE)
    scheduled_date = serializers.DateField()
    scheduled_time = serializers.TimeField()
    notes = serializers.CharField(required=False, allow_blank=True)


class VisitRequestDetailSerializer(serializers.ModelSerializer):
    property = PropertyCardSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    visit_type_display = serializers.CharField(source='get_visit_type_display', read_only=True)

    class Meta:
        model = VisitRequest
        fields = ['id', 'property', 'visit_type', 'visit_type_display', 'status', 'status_display', 'scheduled_date', 'scheduled_time', 'notes', 'created_at']


class PropertyInquiryDetailSerializer(serializers.ModelSerializer):
    property = PropertyCardSerializer(read_only=True)

    class Meta:
        model = PropertyInquiry
        fields = ['id', 'property', 'objective', 'message', 'is_processed', 'created_at']


class MyRequestsResponseSerializer(serializers.Serializer):
    """Écran 15 : Mes demandes (Inquiries, Visites et Projet en cours)."""
    inquiries = PropertyInquiryDetailSerializer(many=True)
    visits = VisitRequestDetailSerializer(many=True)
    project_status = serializers.DictField()


class LeadKanbanItemSerializer(serializers.ModelSerializer):
    consulted_property_title = serializers.CharField(source='consulted_property.title', read_only=True, allow_null=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'full_name', 'phone_number', 'email', 'budget', 'down_payment',
            'preferred_zone', 'property_type', 'stage', 'score', 'temperature',
            'consulted_property_title', 'source', 'last_interaction_at'
        ]
