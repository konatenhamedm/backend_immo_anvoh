"""Ré-exporte les modèles de `infrastructure/models.py` (nécessaire pour dumpdata, voir apps/messaging/models.py)."""

from .infrastructure.models import AnalyticsEvent, ChannelSpend

__all__ = ["AnalyticsEvent", "ChannelSpend"]
