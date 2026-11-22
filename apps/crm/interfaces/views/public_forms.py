"""Formulaires ouverts aux visiteurs (contact, WhatsApp, « Trouver mon bien », visite) : quota `public_forms`."""

from decimal import Decimal

from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.crm.domain.lead_service import advance_stage, find_or_create_lead, rescore
from apps.crm.infrastructure.models import (
    CRMInteraction,
    LeadSource,
    PipelineStage,
    PropertyInquiry,
    VisitRequest,
    VisitRequestStatus,
)
from apps.properties.infrastructure.models import Property, PropertyStatus
from apps.properties.interfaces.serializers import PropertyCardSerializer, favorite_ids_for
from apps.users.interfaces.throttling import ScopedThrottleMixin

from ..serializers import (
    FindMyPropertyInputSerializer,
    FindMyPropertyResponseSerializer,
    PropertyInquiryInputSerializer,
    PropertyInquiryResponseSerializer,
    ScheduleVisitInputSerializer,
    ScheduleVisitResponseSerializer,
    WhatsAppClickTrackResponseSerializer,
    WhatsAppClickTrackSerializer,
)
from ._common import _public_property, _user

# Correspondance types du questionnaire « Trouver mon bien » → types du catalogue.
TYPE_HINTS = {
    "villa": "VILLA",
    "duplex": "DUPLEX",
    "terrain": "TERRAIN",
    "immeuble": "IMMEUBLE",
    "maison": "MAISON",
    "appartement": "APPARTEMENT",
    "f2": "APPARTEMENT",
    "f3": "APPARTEMENT",
    "f4": "APPARTEMENT",
    "meubl": "RESIDENCE_MEUBLEE",
}


@extend_schema(
    tags=["CRM & Écrans"],
    summary="Écran 08 : Demande d'informations sur un bien",
    request=PropertyInquiryInputSerializer,
    responses={201: PropertyInquiryResponseSerializer},
)
class PropertyInquiryView(ScopedThrottleMixin, APIView):
    throttle_scope = "public_forms"
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PropertyInquiryInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        prop = _public_property(data["property_id"])
        lead = find_or_create_lead(
            phone=data["phone_number"],
            user=_user(request),
            full_name=data["full_name"],
            email=data.get("email", ""),
            source=LeadSource.DEMANDE_INFO,
            prop=prop,
            extra={"objective": data["objective"], "preferred_zone": prop.commune},
        )
        inquiry = PropertyInquiry.objects.create(
            property=prop, lead=lead, user=_user(request), objective=data["objective"], message=data.get("message", "")
        )
        CRMInteraction.objects.create(
            lead=lead,
            interaction_type="INQUIRY",
            details=f"Demande d'info sur {prop.reference} ({prop.title}). Objectif : {data['objective']}",
        )
        rescore(lead)
        lead.save()
        return Response(
            {
                "message": "Votre demande d'informations a bien été transmise à un conseiller.",
                "inquiry_id": inquiry.id,
                "lead_id": lead.id,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["CRM & Écrans"],
    summary="Écran 09 : Clic sur le bouton WhatsApp",
    description="Crée ou complète le lead si le visiteur est identifiable (compte ou numéro). Sinon, rien n'est enregistré.",
    request=WhatsAppClickTrackSerializer,
    responses={200: WhatsAppClickTrackResponseSerializer},
)
class WhatsAppClickTrackView(ScopedThrottleMixin, APIView):
    throttle_scope = "public_forms"
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = WhatsAppClickTrackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        prop = Property.objects.filter(id=data["property_id"]).first() if data.get("property_id") else None
        lead = find_or_create_lead(
            phone=data.get("phone_number"),
            user=_user(request),
            full_name=data.get("full_name", ""),
            source=LeadSource.WHATSAPP,
            prop=prop,
        )
        if lead is None:
            return Response({"status": "anonymous", "lead_id": None})
        CRMInteraction.objects.create(
            lead=lead,
            interaction_type="WHATSAPP_CLICK",
            details=f"Clic WhatsApp sur {prop.reference} ({prop.title})" if prop else "Clic WhatsApp général",
        )
        rescore(lead)
        lead.save()
        return Response({"status": "tracked", "lead_id": lead.id})


@extend_schema(
    tags=["CRM & Écrans"],
    summary="Écran 10 : « Trouver mon bien » (questionnaire 7 étapes)",
    request=FindMyPropertyInputSerializer,
    responses={200: FindMyPropertyResponseSerializer},
)
class FindMyPropertyView(ScopedThrottleMixin, APIView):
    throttle_scope = "public_forms"
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = FindMyPropertyInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        is_diaspora = "diaspora" in data["residence_location"].lower()
        lead = find_or_create_lead(
            phone=data["phone_number"],
            user=_user(request),
            full_name=data["full_name"],
            email=data.get("email", ""),
            source=LeadSource.TROUVER_MON_BIEN,
            extra={
                "objective": data["objective"],
                "property_type": data["property_type"],
                "preferred_zone": data["preferred_zone"],
                "timeframe": data["timeframe"],
                "budget": data.get("budget_amount"),
                "down_payment": data.get("down_payment") or None,
                "is_diaspora": is_diaspora,
                "country_of_residence": "Diaspora" if is_diaspora else "Côte d'Ivoire",
            },
        )
        advance_stage(lead, PipelineStage.QUALIFIE)
        rescore(lead)
        lead.save()
        CRMInteraction.objects.create(
            lead=lead,
            interaction_type="QUESTIONNAIRE_7_STEPS",
            details=f"Questionnaire : objectif={lead.objective}, zone={lead.preferred_zone}, délai={lead.timeframe}, score={lead.score}",
        )

        recs = (
            Property.objects.filter(status=PropertyStatus.DISPONIBLE)
            .select_related("owner", "accreditation__notary")
            .prefetch_related("images")
        )
        wanted_type = next((code for hint, code in TYPE_HINTS.items() if hint in data["property_type"].lower()), None)
        for narrowing in (
            {"property_type": wanted_type} if wanted_type else None,
            {"commune__icontains": lead.preferred_zone}
            if lead.preferred_zone and lead.preferred_zone.lower() != "autre"
            else None,
            {"price__lte": lead.budget * Decimal("1.15")} if lead.budget else None,
        ):
            if narrowing and recs.filter(**narrowing).exists():
                recs = recs.filter(**narrowing)
        recommended = list(recs.order_by("-investment_score")[:8])
        return Response(
            {
                "message": f"Nous avons identifié {len(recommended)} opportunités correspondant à votre profil.",
                "lead_id": lead.id,
                "score": lead.score,
                "temperature": lead.temperature,
                "recommended_properties": PropertyCardSerializer(
                    recommended, many=True, context={"request": request, "favorite_ids": favorite_ids_for(request)}
                ).data,
            }
        )


@extend_schema(
    tags=["CRM & Écrans"],
    summary="Écran 16 : Prise de rendez-vous / visite",
    request=ScheduleVisitInputSerializer,
    responses={201: ScheduleVisitResponseSerializer},
)
class ScheduleVisitView(ScopedThrottleMixin, APIView):
    throttle_scope = "public_forms"
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ScheduleVisitInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        prop = _public_property(data["property_id"])
        lead = find_or_create_lead(
            phone=data["phone_number"],
            user=_user(request),
            full_name=data["full_name"],
            email=data.get("email", ""),
            source=LeadSource.VISITE,
            prop=prop,
        )
        duplicate = (
            VisitRequest.objects.filter(
                property=prop,
                lead=lead,
                scheduled_date=data["scheduled_date"],
                scheduled_time=data["scheduled_time"],
            )
            .exclude(status=VisitRequestStatus.ANNULEE)
            .first()
        )
        if duplicate:
            return Response(
                {"message": "Cette visite est déjà enregistrée.", "visit_id": duplicate.id, "lead_id": lead.id}
            )
        visit = VisitRequest.objects.create(
            property=prop,
            lead=lead,
            user=_user(request),
            visit_type=data["visit_type"],
            scheduled_date=data["scheduled_date"],
            scheduled_time=data["scheduled_time"],
            notes=data.get("notes", ""),
        )
        advance_stage(lead, PipelineStage.RDV)
        rescore(lead)
        lead.save()
        CRMInteraction.objects.create(
            lead=lead,
            interaction_type="VISIT_SCHEDULED",
            details=f"Visite {visit.get_visit_type_display()} le {data['scheduled_date']} à {data['scheduled_time']:%H:%M} sur {prop.reference}",
        )
        return Response(
            {
                "message": "Votre demande de rendez-vous est enregistrée. Le conseiller vous confirme le créneau.",
                "visit_id": visit.id,
                "lead_id": lead.id,
            },
            status=status.HTTP_201_CREATED,
        )
