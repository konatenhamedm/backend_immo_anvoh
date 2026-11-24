"""Éléments partagés par les vues du module `crm` (aucune vue ici)."""

from django.shortcuts import get_object_or_404

from apps.analytics.application.recorder import record
from apps.crm.infrastructure.models import AcquisitionChannel
from apps.properties.infrastructure.models import PUBLIC_STATUSES, Property


def _user(request):
    return request.user if request.user.is_authenticated else None


def _attribution(data) -> dict:
    """Origine marketing envoyée par le site ; à défaut de canal, le prospect vient du site Web."""
    att = dict(data.get("attribution") or {})
    att["channel"] = att.get("channel") or AcquisitionChannel.SITE_WEB
    return att


def _track(request, name, data, **properties):
    """Enregistre un événement de conversion (le canal vient de l'attribution fournie par le site)."""
    record(name, user=_user(request), channel=_attribution(data)["channel"], properties=properties)


def _public_property(property_id):
    return get_object_or_404(
        Property.objects.select_related("assigned_agent"), id=property_id, status__in=PUBLIC_STATUSES
    )


# Relations lues par PropertyCardSerializer pour chaque bien : à charger d'un coup (sinon une requête par ligne).
PROPERTY_CARD_RELATED = ("property__owner", "property__assigned_agent", "property__accreditation__notary")
