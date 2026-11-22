"""Quotas par type d'endpoint, en plus des quotas généraux (anonyme / connecté) de settings.py.

Un view déclare `throttle_scope = '<scope>'` ; la cadence du scope est dans `DEFAULT_THROTTLE_RATES`.
  - `auth`         : connexion, inscription, changement de mot de passe (freine les essais de mots de passe)
  - `public_forms` : formulaires ouverts aux visiteurs (demande d'informations, WhatsApp, visite, « Trouver mon bien »)
"""

from rest_framework.settings import api_settings
from rest_framework.throttling import ScopedRateThrottle


class ScopedThrottleMixin:
    throttle_classes = [*api_settings.DEFAULT_THROTTLE_CLASSES, ScopedRateThrottle]
