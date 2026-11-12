from rest_framework import serializers

from apps.rentals.infrastructure.models import Lease, OwnerPayout, RentPayment


class LeaseSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)
    property_reference = serializers.CharField(source='property.reference', read_only=True)

    class Meta:
        model = Lease
        fields = ['id', 'property', 'property_title', 'property_reference', 'tenant_label', 'monthly_rent',
                  'occupancy_rate', 'management_fee_rate', 'start_date', 'end_date', 'is_active']


class RentPaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = RentPayment
        fields = ['id', 'lease', 'period', 'amount', 'status', 'status_display', 'paid_at']

    def validate_period(self, value):
        return value.replace(day=1)


class OwnerPayoutSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OwnerPayout
        fields = ['id', 'owner', 'amount', 'reference', 'payout_date', 'status', 'status_display']
