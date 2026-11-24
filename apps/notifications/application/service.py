"""
Envoi des notifications : écrit la notification (visible dans l'application) puis envoie l'e-mail.

Principes :
- JAMAIS d'exception vers l'appelant : une notification ratée ne doit pas faire échouer une demande de visite ;
- l'e-mail part après validation de la transaction (`on_commit`) : pas d'e-mail pour une action annulée ;
- pas de notification pendant les commandes de chargement de données (seed_data, load_demo_data…) ;
- canaux supplémentaires (SMS, WhatsApp, push Firebase) : ajouter une fonction dans CHANNELS ci-dessous.
"""

import logging
import sys
from collections.abc import Iterable

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.notifications.domain import kinds
from apps.notifications.infrastructure.models import Notification
from apps.users.infrastructure.models import User, UserRole

log = logging.getLogger(__name__)

# Commandes qui fabriquent des données en masse : on n'envoie rien (sinon des centaines de messages fictifs).
SILENT_COMMANDS = {
    "seed_data",
    "seed_demo_scenarios",
    "load_demo_data",
    "export_demo_data",
    "loaddata",
    "flush",
    "migrate",
}


def suppressed() -> bool:
    return len(sys.argv) > 1 and sys.argv[1] in SILENT_COMMANDS and not getattr(settings, "NOTIFICATIONS_FORCE", False)


def absolute(path: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}{path}" if path.startswith("/") else path


def _email_channel(n: Notification) -> bool:
    user = n.user
    if not user.email:
        return False
    link = f"\n\n{absolute(n.url)}" if n.url else ""
    send_mail(
        subject=n.title,
        message=f"{n.body}{link}\n\n— THIEBBRO IMMO",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return True


# Canaux de diffusion, dans l'ordre. Chacun reçoit la notification et renvoie True s'il l'a envoyée.
CHANNELS = [_email_channel]


def _deliver(notification_id) -> None:
    try:
        n = Notification.objects.select_related("user").get(pk=notification_id)
        if n.emailed_at is None and any(channel(n) for channel in CHANNELS):
            Notification.objects.filter(pk=n.pk).update(emailed_at=timezone.now())
    except Exception:  # noqa: BLE001 — une panne d'envoi ne doit jamais remonter à l'utilisateur
        log.exception("Envoi de notification impossible (%s)", notification_id)


def notify(user, kind: str, title: str, body: str = "", url: str = "", dedupe_key: str = "") -> Notification | None:
    """Notifie un utilisateur. Renvoie la notification créée, ou None (désactivée, doublon, utilisateur inactif…)."""
    if suppressed() or user is None or not user.is_active:
        return None
    if not kinds.wants(kind, user.notifications_enabled, user.notification_preferences):
        return None
    try:
        with transaction.atomic():
            n = Notification.objects.create(
                user=user, kind=kind, title=title[:200], body=body, url=url, dedupe_key=dedupe_key
            )
    except IntegrityError:  # même notification déjà envoyée (dedupe_key)
        return None
    except Exception:  # noqa: BLE001
        log.exception("Création de notification impossible")
        return None
    transaction.on_commit(lambda: _deliver(n.pk))
    return n


def team_recipients(lead=None, prop=None) -> Iterable[User]:
    """Le conseiller du prospect, sinon celui du bien, sinon tous les administrateurs actifs."""
    agent = (lead.assigned_agent if lead is not None else None) or (prop.assigned_agent if prop is not None else None)
    if agent is not None and agent.is_active:
        return [agent]
    return list(User.objects.filter(role=UserRole.ADMIN, is_active=True))


def notify_team(kind: str, title: str, body: str, url: str, lead=None, prop=None, dedupe: str = "") -> int:
    count = 0
    for user in team_recipients(lead, prop):
        key = f"{dedupe}:{user.pk}" if dedupe else ""
        if notify(user, kind, title, body, url, dedupe_key=key):
            count += 1
    return count


def notify_lead_event(lead, kind: str, title: str, body: str, dedupe: str = "", prop=None) -> int:
    """Prévient l'équipe d'un événement sur un prospect ; le lien ouvre la fiche prospect du back-office."""
    return notify_team(kind, title, body, f"/admin/crm?lead={lead.pk}", lead=lead, prop=prop, dedupe=dedupe)
