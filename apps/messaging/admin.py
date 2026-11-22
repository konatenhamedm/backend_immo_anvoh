from django.contrib import admin

from .infrastructure.models import Conversation, ConversationParticipant, Message


class ParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 0


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("sender", "body", "created_at")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("subject", "property", "updated_at")
    search_fields = ("subject", "property__title")
    inlines = [ParticipantInline, MessageInline]
