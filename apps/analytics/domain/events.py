"""Événements mesurés (spécification §31) et règles pures de validation (aucune dépendance Django)."""

# Événements que le NAVIGATEUR peut déclarer (liste fermée : tout autre nom est refusé).
SESSION_START = "SESSION_START"  # utilisateurs actifs
SEARCH = "SEARCH"  # recherches
PROPERTY_VIEW = "PROPERTY_VIEW"  # biens consultés
SIGNUP = "SIGNUP"  # inscriptions
APP_INSTALLED = "APP_INSTALLED"  # téléchargements (installation de la PWA)
SIMULATION_CAPACITY = "SIMULATION_CAPACITY"  # simulations
SIMULATION_RENTABILITY = "SIMULATION_RENTABILITY"

CLIENT_EVENTS = {
    SESSION_START,
    SEARCH,
    PROPERTY_VIEW,
    SIGNUP,
    APP_INSTALLED,
    SIMULATION_CAPACITY,
    SIMULATION_RENTABILITY,
}

# Événements enregistrés UNIQUEMENT par le serveur (jamais acceptés du navigateur : ils ne se falsifient pas).
FAVORITE_ADD = "FAVORITE_ADD"  # favoris
INQUIRY = "INQUIRY"  # demandes
WHATSAPP_CLICK = "WHATSAPP_CLICK"  # clics WhatsApp
VISIT_REQUESTED = "VISIT_REQUESTED"  # visites demandées
LEAD_CREATED = "LEAD_CREATED"  # leads
SALE = "SALE"  # conversions

SERVER_EVENTS = {FAVORITE_ADD, INQUIRY, WHATSAPP_CLICK, VISIT_REQUESTED, LEAD_CREATED, SALE}
ALL_EVENTS = CLIENT_EVENTS | SERVER_EVENTS

# Une statistique ne doit JAMAIS contenir de donnée personnelle : ces clés sont supprimées d'office.
FORBIDDEN_KEYS = {
    "email",
    "mail",
    "phone",
    "phone_number",
    "telephone",
    "tel",
    "name",
    "full_name",
    "first_name",
    "last_name",
    "password",
    "token",
    "access",
    "refresh",
    "message",
}

MAX_PROPERTIES = 12
MAX_VALUE_LENGTH = 120


def clean_properties(raw) -> dict:
    """Garde au plus 12 propriétés à plat (texte, nombre, booléen), sans clé interdite ; textes tronqués à 120 caractères."""
    if not isinstance(raw, dict):
        return {}
    out: dict = {}
    for key, value in raw.items():
        k = str(key)[:40]
        if k.lower() in FORBIDDEN_KEYS or len(out) >= MAX_PROPERTIES:
            continue
        if isinstance(value, bool) or isinstance(value, (int, float)):
            out[k] = value
        elif isinstance(value, str):
            out[k] = value[:MAX_VALUE_LENGTH]
    return out
