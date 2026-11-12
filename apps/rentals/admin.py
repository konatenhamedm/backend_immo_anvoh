from django.contrib import admin

from .infrastructure.models import Lease, OwnerPayout, RentPayment


class RentPaymentInline(admin.TabularInline):
    model = RentPayment
    extra = 0


@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ('property', 'tenant_label', 'monthly_rent', 'occupancy_rate', 'is_active')
    list_filter = ('is_active',)
    inlines = [RentPaymentInline]


@admin.register(OwnerPayout)
class OwnerPayoutAdmin(admin.ModelAdmin):
    list_display = ('owner', 'amount', 'reference', 'payout_date', 'status')
    list_filter = ('status',)
