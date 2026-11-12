from django.contrib import admin

from .infrastructure.models import AccreditationFile, Notary, PropertyDocument


@admin.register(Notary)
class NotaryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'office', 'city', 'is_active', 'user')
    list_filter = ('is_active', 'city')
    search_fields = ('full_name', 'office', 'email')


@admin.register(AccreditationFile)
class AccreditationFileAdmin(admin.ModelAdmin):
    list_display = ('property', 'notary', 'step', 'status', 'certification_level', 'submitted_at')
    list_filter = ('status', 'step', 'notary')
    search_fields = ('property__reference', 'property__title')


@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = ('property', 'doc_type', 'status', 'uploaded_at')
    list_filter = ('doc_type', 'status')
