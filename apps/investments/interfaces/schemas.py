"""Schémas OpenAPI des réponses agrégées du module `investments` (documentation uniquement)."""

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

from .serializers import InvestmentDocumentSerializer, ScheduleEntrySerializer, SubscriptionSerializer

_money = lambda: serializers.DecimalField(max_digits=16, decimal_places=2)

InvestmentStatsSchema = inline_serializer(
    "InvestmentStats",
    {
        "aum": _money(),
        "subscribers": serializers.IntegerField(),
        "subscriptions_this_month": serializers.IntegerField(),
        "pending_payments": serializers.IntegerField(),
        "income_paid_year": _money(),
    },
)

MyInvestmentsSchema = inline_serializer(
    "MyInvestments",
    {
        "summary": inline_serializer(
            "MyInvestmentsSummary",
            {
                "invested": _money(),
                "estimated_value": _money(),
                "income_year": _money(),
                "next_due": ScheduleEntrySerializer(allow_null=True),
            },
        ),
        "subscriptions": SubscriptionSerializer(many=True),
        "schedule": ScheduleEntrySerializer(many=True),
        "documents": InvestmentDocumentSerializer(many=True),
    },
)
