"""Enregistrement des événements. Ne lève JAMAIS d'exception : la mesure ne doit pas faire échouer une action."""

import logging

from apps.analytics.domain.events import ALL_EVENTS, clean_properties
from apps.analytics.infrastructure.models import AnalyticsEvent
from apps.notifications.application.service import suppressed

log = logging.getLogger(__name__)


def record(name: str, *, user=None, anonymous_id: str = "", channel: str = "", path: str = "", properties: dict | None = None):
    """Enregistre un événement (sauf pendant seed_data / load_demo_data). Renvoie l'événement, ou None."""
    if name not in ALL_EVENTS or suppressed():
        return None
    try:
        return AnalyticsEvent.objects.create(
            name=name,
            user=user if getattr(user, "is_authenticated", False) else None,
            anonymous_id=(anonymous_id or "")[:64],
            channel=channel or "",
            path=(path or "")[:200],
            properties=clean_properties(properties),
        )
    except Exception:  # noqa: BLE001
        log.exception("Enregistrement d'événement impossible (%s)", name)
        return None
