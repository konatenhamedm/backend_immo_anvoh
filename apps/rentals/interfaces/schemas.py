"""Schémas OpenAPI des réponses agrégées du module `rentals` (documentation uniquement)."""

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

from apps.properties.interfaces.schemas import monthly_points
from .serializers import OwnerPayoutSerializer

_money = lambda: serializers.DecimalField(max_digits=14, decimal_places=2)

RentalSummarySchema = inline_serializer(
    "RentalSummary",
    {
        "month_label": serializers.CharField(),
        "month_revenue": _money(),
        "month_delta_pct": serializers.FloatField(allow_null=True),
        "year_total": _money(),
        "occupancy_rate": serializers.IntegerField(allow_null=True),
        "next_payout": OwnerPayoutSerializer(allow_null=True),
        "monthly": monthly_points(),
        "payouts": OwnerPayoutSerializer(many=True),
        "leases": inline_serializer(
            "RentalLeaseRow",
            {
                "lease_id": serializers.UUIDField(),
                "property": inline_serializer(
                    "RentalLeaseProperty",
                    {
                        "id": serializers.UUIDField(),
                        "reference": serializers.CharField(),
                        "title": serializers.CharField(),
                        "slug": serializers.CharField(),
                        "commune": serializers.CharField(),
                        "neighborhood": serializers.CharField(),
                        "cover_image": serializers.URLField(allow_null=True),
                    },
                ),
                "tenant": serializers.CharField(),
                "monthly_rent": _money(),
                "occupancy_rate": serializers.IntegerField(),
                "current_status": serializers.ChoiceField(choices=["PAYE", "EN_RETARD", "IMPAYE", "A_VENIR"]),
            },
            many=True,
        ),
    },
)
