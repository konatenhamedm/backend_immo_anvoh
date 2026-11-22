from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.rentals.infrastructure.models import Lease, OwnerPayout, RentPayment, RentStatus


class LeaseSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source="property.title", read_only=True)
    property_reference = serializers.CharField(source="property.reference", read_only=True)

    class Meta:
        model = Lease
        fields = [
            "id",
            "property",
            "property_title",
            "property_reference",
            "tenant_label",
            "monthly_rent",
            "occupancy_rate",
            "management_fee_rate",
            "start_date",
            "end_date",
            "is_active",
        ]

    def validate_occupancy_rate(self, value):
        if value > 100:
            raise serializers.ValidationError("Le taux d'occupation ne peut pas dépasser 100 %.")
        return value

    def validate_management_fee_rate(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Les honoraires doivent être compris entre 0 et 100 %.")
        return value

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "La fin du bail ne peut pas précéder son début."})
        return attrs


class RentPaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    property_reference = serializers.CharField(source="lease.property.reference", read_only=True)
    property_title = serializers.CharField(source="lease.property.title", read_only=True)
    tenant_label = serializers.CharField(source="lease.tenant_label", read_only=True)

    class Meta:
        model = RentPayment
        fields = [
            "id",
            "lease",
            "property_reference",
            "property_title",
            "tenant_label",
            "period",
            "amount",
            "status",
            "status_display",
            "paid_at",
        ]

    def validate_period(self, value):
        return value.replace(day=1)

    def validate(self, attrs):
        # Un loyer marqué « payé » porte toujours sa date d'encaissement (aujourd'hui par défaut).
        status = attrs.get("status", getattr(self.instance, "status", RentStatus.PAYE))
        paid_at = attrs.get("paid_at", getattr(self.instance, "paid_at", None))
        if status == RentStatus.PAYE and not paid_at:
            attrs["paid_at"] = timezone.localdate()
        return attrs


class OwnerPayoutSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = OwnerPayout
        fields = ["id", "owner", "owner_name", "amount", "reference", "payout_date", "status", "status_display"]

    @extend_schema_field({"type": "string"})
    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}".strip() or obj.owner.email
