from django.contrib import admin
from .infrastructure.models import Lead, CRMInteraction, PropertyInquiry, VisitRequest

class CRMInteractionInline(admin.TabularInline):
    model = CRMInteraction
    extra = 1

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'stage', 'score', 'temperature', 'source', 'assigned_agent', 'created_at')
    list_filter = ('stage', 'temperature', 'source', 'assigned_agent', 'is_diaspora')
    search_fields = ('full_name', 'phone_number', 'email', 'preferred_zone')
    list_editable = ('stage', 'assigned_agent')
    inlines = [CRMInteractionInline]

@admin.register(PropertyInquiry)
class PropertyInquiryAdmin(admin.ModelAdmin):
    list_display = ('property', 'lead', 'objective', 'is_processed', 'created_at')
    list_filter = ('is_processed', 'objective')
    search_fields = ('lead__full_name', 'property__title')
    list_editable = ('is_processed',)

@admin.register(VisitRequest)
class VisitRequestAdmin(admin.ModelAdmin):
    list_display = ('property', 'lead', 'scheduled_date', 'scheduled_time', 'visit_type', 'status')
    list_filter = ('status', 'visit_type', 'scheduled_date')
    search_fields = ('lead__full_name', 'property__title')
    list_editable = ('status',)
