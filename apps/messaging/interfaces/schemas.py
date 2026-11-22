"""Schémas OpenAPI des réponses agrégées du module `messaging` (documentation uniquement)."""

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

UnreadCountSchema = inline_serializer("UnreadCount", {"unread": serializers.IntegerField()})
