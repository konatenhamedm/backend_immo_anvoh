"""Schémas OpenAPI des réponses agrégées du module `properties` (documentation uniquement)."""

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

# Une seule classe par composant : réutiliser la même classe évite les doublons de noms dans le schéma.
_MonthlyPoint = type(
    inline_serializer(
        "MonthlyPoint",
        {
            "month": serializers.CharField(),
            "value": serializers.FloatField(),
        },
    )
)
_Choice = type(
    inline_serializer(
        "PropertyChoice",
        {
            "value": serializers.CharField(),
            "label": serializers.CharField(),
        },
    )
)


def monthly_points():
    return _MonthlyPoint(many=True)


def choices():
    return _Choice(many=True)


CatalogMetaSchema = inline_serializer(
    "CatalogMeta",
    {
        "communes": serializers.ListField(child=serializers.CharField()),
        "property_types": choices(),
        "transactions": choices(),
        "title_deeds": choices(),
    },
)

PropertySlugSchema = inline_serializer(
    "PropertySlug",
    {
        "slug": serializers.CharField(),
        "updated_at": serializers.DateTimeField(),
    },
    many=True,
)

OwnerDashboardSchema = inline_serializer(
    "OwnerDashboard",
    {
        "properties_total": serializers.IntegerField(),
        "properties_online": serializers.IntegerField(),
        "views_total": serializers.IntegerField(),
        "leads_total": serializers.IntegerField(),
        "visits_pending": serializers.IntegerField(),
        "visits_upcoming": serializers.IntegerField(),
        "accreditations_in_progress": serializers.IntegerField(),
        "monthly_leads": monthly_points(),
    },
)


class ImageCoverSerializer(serializers.Serializer):
    """Corps de `PATCH properties/images/<id>/` : mettre la photo en couverture."""

    is_cover = serializers.BooleanField()
