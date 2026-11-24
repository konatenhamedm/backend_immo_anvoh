"""
Types de notifications et règles pures (aucune dépendance Django) : préférences, libellés.

Deux familles :
- notifications CLIENT (nouveau bien, baisse de prix, visite confirmée) : soumises aux préférences de l'utilisateur
  (`notifications_enabled` et `notification_preferences` du profil) ;
- notifications ÉQUIPE (nouveau prospect, prospect qualifié, visite demandée, relance) : toujours envoyées.
"""

NEW_MATCH = "NEW_MATCH"
PRICE_DROP = "PRICE_DROP"
VISIT_CONFIRMED = "VISIT_CONFIRMED"
LEAD_NEW = "LEAD_NEW"
LEAD_QUALIFIED = "LEAD_QUALIFIED"
VISIT_REQUESTED = "VISIT_REQUESTED"
FOLLOWUP_DUE = "FOLLOWUP_DUE"

KIND_CHOICES = [
    (NEW_MATCH, "Nouveau bien correspondant à une recherche"),
    (PRICE_DROP, "Baisse de prix d'un favori"),
    (VISIT_CONFIRMED, "Visite confirmée"),
    (LEAD_NEW, "Nouveau prospect"),
    (LEAD_QUALIFIED, "Nouveau prospect qualifié"),
    (VISIT_REQUESTED, "Demande de visite"),
    (FOLLOWUP_DUE, "Relance à effectuer"),
]

# Clé de préférence (profil utilisateur) pour chaque type client ; les types équipe n'en ont pas.
PREFERENCE_KEY = {
    NEW_MATCH: "new_matches",
    PRICE_DROP: "price_drops",
    VISIT_CONFIRMED: "visit_reminders",
}

DAYS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def wants(kind: str, enabled: bool, preferences: dict | None) -> bool:
    """Cet utilisateur veut-il recevoir ce type de notification ? (clé absente = oui)"""
    key = PREFERENCE_KEY.get(kind)
    if key is None:  # notification d'équipe : toujours
        return True
    if not enabled:
        return False
    return bool((preferences or {}).get(key, True))


def hour_fr(hour: int, minute: int) -> str:
    """10:00 → « 10h » ; 14:30 → « 14h30 » (écriture de la spécification : « samedi à 10h »)."""
    return f"{hour}h" if minute == 0 else f"{hour}h{minute:02d}"
