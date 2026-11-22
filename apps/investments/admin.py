from django.contrib import admin

from .infrastructure.models import InvestmentDocument, InvestmentPlan, ScheduleEntry, Subscription


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "min_ticket", "risk", "status", "allows_instalments", "order")
    list_editable = ("status", "order")
    prepopulated_fields = {"code": ("name",)}


class ScheduleEntryInline(admin.TabularInline):
    model = ScheduleEntry
    extra = 0


class InvestmentDocumentInline(admin.TabularInline):
    model = InvestmentDocument
    extra = 0


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "plan", "amount", "status", "payment_method", "created_at")
    list_filter = ("status", "plan", "payment_method")
    search_fields = ("reference", "user__email", "user__last_name")
    inlines = [ScheduleEntryInline, InvestmentDocumentInline]
