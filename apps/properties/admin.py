from django.contrib import admin
from .infrastructure.models import (
    Property, PropertyImage, PropertyFavorite,
    DevelopmentProject, ProjectLot
)

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

class ProjectLotInline(admin.TabularInline):
    model = ProjectLot
    extra = 2

@admin.register(DevelopmentProject)
class DevelopmentProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'developer_name', 'commune', 'starting_price', 'total_lots_count', 'delivery_date', 'is_featured')
    list_filter = ('commune', 'is_featured')
    search_fields = ('name', 'developer_name', 'commune')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProjectLotInline]


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('reference', 'title', 'property_type', 'typology', 'commune', 'price', 'status', 'verification_status', 'is_featured', 'is_selected_investment')
    list_filter = ('property_type', 'typology', 'status', 'verification_status', 'commune', 'is_featured', 'is_selected_investment')
    search_fields = ('reference', 'title', 'commune', 'neighborhood', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PropertyImageInline]


@admin.register(PropertyFavorite)
class PropertyFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'created_at')
    search_fields = ('user__email', 'property__title')
