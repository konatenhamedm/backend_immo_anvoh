from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.investments.domain.services import paid_amount
from apps.investments.infrastructure.models import (
    MOBILE_MONEY,
    InvestmentDocument,
    InvestmentPlan,
    PaymentMethod,
    ScheduleEntry,
    Subscription,
)


class InvestmentPlanSerializer(serializers.ModelSerializer):
    risk_display = serializers.CharField(source="get_risk_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    features = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = InvestmentPlan
        fields = [
            "id",
            "code",
            "name",
            "tagline",
            "description",
            "min_ticket",
            "duration_label",
            "target_yield_label",
            "risk",
            "risk_display",
            "features",
            "allows_instalments",
            "highlight",
            "status",
            "status_display",
            "order",
        ]


class InvestmentPlanAdminSerializer(InvestmentPlanSerializer):
    subscribers = serializers.IntegerField(read_only=True, default=0)
    aum = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True, default=0)

    class Meta(InvestmentPlanSerializer.Meta):
        fields = InvestmentPlanSerializer.Meta.fields + ["subscribers", "aum"]


class SubscribeSerializer(serializers.Serializer):
    plan = serializers.SlugRelatedField(slug_field="code", queryset=InvestmentPlan.objects.all())
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    months = serializers.IntegerField(required=False, allow_null=True)
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    payment_phone = serializers.CharField(required=False, allow_blank=True, max_length=30)
    accept_terms = serializers.BooleanField()

    def validate(self, data):
        if not data.get("accept_terms"):
            raise serializers.ValidationError({"accept_terms": "Vous devez accepter la notice d'information du plan."})
        if data["payment_method"] in MOBILE_MONEY and not data.get("payment_phone"):
            raise serializers.ValidationError({"payment_phone": "Numéro mobile money requis."})
        return data


class ScheduleEntrySerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    plan_name = serializers.CharField(source="subscription.plan.name", read_only=True)

    class Meta:
        model = ScheduleEntry
        fields = [
            "id",
            "kind",
            "kind_display",
            "label",
            "plan_name",
            "due_date",
            "amount",
            "status",
            "status_display",
            "payment_reference",
            "settled_at",
        ]


class InvestmentDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = InvestmentDocument
        fields = ["id", "title", "file_url", "created_at"]

    @extend_schema_field({"type": "string", "format": "uri", "nullable": True})
    def get_file_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request and obj.file else None


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = InvestmentPlanSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_method_display = serializers.CharField(source="get_payment_method_display", read_only=True)
    paid = serializers.SerializerMethodField()
    next_entry = serializers.SerializerMethodField()
    subscriber = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "id",
            "reference",
            "plan",
            "asset_label",
            "amount",
            "months",
            "paid",
            "estimated_value",
            "payment_method",
            "payment_method_display",
            "status",
            "status_display",
            "next_entry",
            "subscriber",
            "created_at",
            "activated_at",
        ]

    @extend_schema_field({"type": "string", "format": "decimal"})
    def get_paid(self, obj):
        return paid_amount(obj)

    @extend_schema_field(ScheduleEntrySerializer(allow_null=True))
    def get_next_entry(self, obj):
        upcoming = sorted(
            (e for e in obj.entries.all() if e.status in ("A_VENIR", "EN_VALIDATION", "PROGRAMME")),
            key=lambda e: e.due_date,
        )
        return ScheduleEntrySerializer(upcoming[0]).data if upcoming else None

    @extend_schema_field(
        {
            "type": "object",
            "nullable": False,
            "properties": {"id": {"type": "integer"}, "name": {"type": "string"}, "email": {"type": "string"}},
        }
    )
    def get_subscriber(self, obj):
        u = obj.user
        return {"id": u.id, "name": f"{u.first_name} {u.last_name}".strip() or u.email, "email": u.email}


class SubscriptionAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ["asset_label", "estimated_value", "status"]


class RevenueEntrySerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=1)
    due_date = serializers.DateField()
    label = serializers.CharField(max_length=200)
    received = serializers.BooleanField(default=False)


class ConfirmPaymentSerializer(serializers.Serializer):
    reference = serializers.CharField(required=False, allow_blank=True, max_length=80, default="")
