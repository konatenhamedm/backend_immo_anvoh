from decimal import Decimal

from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.crm.infrastructure.models import (
    CRMInteraction,
    Lead,
    LeadSource,
    PipelineStage,
    PropertyInquiry,
    SearchAlert,
    VisitRequest,
    VisitRequestType,
)
from apps.properties.interfaces.serializers import PropertyCardSerializer


class PropertyInquiryInputSerializer(serializers.Serializer):
    """Écran 08 : Formulaire de demande d'informations sur une fiche bien."""

    property_id = serializers.UUIDField()
    full_name = serializers.CharField(max_length=200)
    phone_number = serializers.CharField(max_length=30)
    email = serializers.EmailField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    objective = serializers.ChoiceField(choices=["Habiter", "Investir", "Louer", "Autre"], default="Habiter")


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
    lead_id = serializers.UUIDField(allow_null=True)


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

    objective = serializers.CharField(max_length=100)  # Étape 1
    property_type = serializers.CharField(max_length=100)  # Étape 2
    preferred_zone = serializers.CharField(max_length=150)  # Étape 3
    budget_range = serializers.CharField(max_length=100)  # Étape 4 (ex: "50-80 M")
    budget_amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    down_payment = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, default=Decimal("0")
    )  # Étape 5
    timeframe = serializers.CharField(max_length=100)  # Étape 6
    residence_location = serializers.CharField(max_length=100)  # Étape 7 ("Côte d'Ivoire" ou "Diaspora")


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

    def validate_scheduled_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("La date de visite ne peut pas être passée.")
        return value


class VisitRequestDetailSerializer(serializers.ModelSerializer):
    property = PropertyCardSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    visit_type_display = serializers.CharField(source="get_visit_type_display", read_only=True)
    visitor_name = serializers.CharField(source="lead.full_name", read_only=True)

    class Meta:
        model = VisitRequest
        fields = [
            "id",
            "property",
            "visitor_name",
            "visit_type",
            "visit_type_display",
            "status",
            "status_display",
            "scheduled_date",
            "scheduled_time",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "property", "visit_type", "created_at"]


class VisitUpdateSerializer(serializers.ModelSerializer):
    """Confirmer, reprogrammer, annuler ou clore une visite (propriétaire du bien ou équipe)."""

    class Meta:
        model = VisitRequest
        fields = ["status", "scheduled_date", "scheduled_time", "notes"]

    def validate_scheduled_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("La date de visite ne peut pas être passée.")
        return value


class PropertyInquiryDetailSerializer(serializers.ModelSerializer):
    property = PropertyCardSerializer(read_only=True)
    lead_name = serializers.CharField(source="lead.full_name", read_only=True)
    lead_phone = serializers.CharField(source="lead.phone_number", read_only=True)

    class Meta:
        model = PropertyInquiry
        fields = [
            "id",
            "property",
            "lead",
            "lead_name",
            "lead_phone",
            "objective",
            "message",
            "is_processed",
            "created_at",
        ]
        read_only_fields = ["id", "property", "lead", "objective", "message", "created_at"]


class MyRequestsResponseSerializer(serializers.Serializer):
    """Écran 15 : Mes demandes (Inquiries, Visites et Projet en cours)."""

    inquiries = PropertyInquiryDetailSerializer(many=True)
    visits = VisitRequestDetailSerializer(many=True)
    project_status = serializers.DictField()


class LeadKanbanItemSerializer(serializers.ModelSerializer):
    consulted_property_title = serializers.CharField(source="consulted_property.title", read_only=True, allow_null=True)
    consulted_property_reference = serializers.CharField(
        source="consulted_property.reference", read_only=True, allow_null=True
    )
    consulted_property_slug = serializers.CharField(source="consulted_property.slug", read_only=True, allow_null=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)
    temperature_display = serializers.CharField(source="get_temperature_display", read_only=True)
    agent = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            "id",
            "full_name",
            "phone_number",
            "whatsapp_number",
            "email",
            "is_diaspora",
            "country_of_residence",
            "objective",
            "budget",
            "down_payment",
            "timeframe",
            "preferred_zone",
            "property_type",
            "stage",
            "stage_display",
            "score",
            "temperature",
            "temperature_display",
            "consulted_property",
            "consulted_property_title",
            "consulted_property_reference",
            "consulted_property_slug",
            "source",
            "source_display",
            "assigned_agent",
            "agent",
            "next_action",
            "commercial_notes",
            "last_interaction_at",
            "created_at",
        ]
        read_only_fields = ["id", "score", "temperature", "last_interaction_at", "created_at", "source"]

    @extend_schema_field(
        {
            "type": "object",
            "nullable": True,
            "properties": {"id": {"type": "integer"}, "name": {"type": "string"}, "initials": {"type": "string"}},
        }
    )
    def get_agent(self, obj):
        a = obj.assigned_agent
        if not a:
            return None
        name = f"{a.first_name} {a.last_name}".strip() or a.email
        initials = "".join(p[0] for p in name.split()[:2]).upper()
        return {"id": a.id, "name": name, "initials": initials}


class CRMInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CRMInteraction
        fields = ["id", "interaction_type", "details", "created_at"]


class LeadDetailSerializer(LeadKanbanItemSerializer):
    """Fiche prospect complète : historique, demandes et visites."""

    interactions = CRMInteractionSerializer(many=True, read_only=True)
    visits = VisitRequestDetailSerializer(many=True, read_only=True)
    inquiries = PropertyInquiryDetailSerializer(many=True, read_only=True)

    class Meta(LeadKanbanItemSerializer.Meta):
        fields = LeadKanbanItemSerializer.Meta.fields + ["interactions", "visits", "inquiries"]


class LeadNoteSerializer(serializers.Serializer):
    interaction_type = serializers.ChoiceField(choices=["NOTE", "CALL", "EMAIL", "WHATSAPP"], default="NOTE")
    details = serializers.CharField(max_length=2000)


class SearchAlertSerializer(serializers.ModelSerializer):
    frequency_display = serializers.CharField(source="get_frequency_display", read_only=True)
    label = serializers.SerializerMethodField()

    class Meta:
        model = SearchAlert
        fields = [
            "id",
            "transaction",
            "property_type",
            "commune",
            "max_budget",
            "frequency",
            "frequency_display",
            "label",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_transaction(self, value):
        if value and value not in ("VENTE", "LOCATION"):
            raise serializers.ValidationError("VENTE, LOCATION ou vide.")
        return value

    def get_label(self, obj) -> str:
        from apps.properties.infrastructure.models import PropertyType

        parts = [
            {"VENTE": "Achat", "LOCATION": "Location"}.get(obj.transaction, "Achat ou location"),
            dict(PropertyType.choices).get(obj.property_type, "tous types") if obj.property_type else "tous types",
            obj.commune or "toutes communes",
        ]
        return " · ".join(parts)


class LeadCreateSerializer(serializers.Serializer):
    """Saisie manuelle d'un prospect par l'équipe (salon, appel entrant, recommandation…)."""

    full_name = serializers.CharField(max_length=200)
    phone_number = serializers.CharField(max_length=30)
    email = serializers.EmailField(required=False, allow_blank=True)
    consulted_property = serializers.UUIDField(required=False, allow_null=True)
    budget = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, allow_null=True)
    source = serializers.ChoiceField(choices=LeadSource.choices, default=LeadSource.AUTRE)
    stage = serializers.ChoiceField(choices=PipelineStage.choices, default=PipelineStage.NOUVEAU)
    assign_to_me = serializers.BooleanField(default=False)
    commercial_notes = serializers.CharField(required=False, allow_blank=True)
