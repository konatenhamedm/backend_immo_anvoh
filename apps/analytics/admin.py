from django.contrib import admin

from .infrastructure.models import AnalyticsEvent, ChannelSpend


@admin.register(ChannelSpend)
class ChannelSpendAdmin(admin.ModelAdmin):
    list_display = ("channel", "month", "amount", "note")
    list_filter = ("channel",)


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("name", "occurred_at", "channel", "path", "user")
    list_filter = ("name", "channel")
    date_hierarchy = "occurred_at"
    readonly_fields = [f.name for f in AnalyticsEvent._meta.fields]

    def has_add_permission(self, request):
        return False
