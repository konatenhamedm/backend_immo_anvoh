"""
Écouteurs : déclenchent les notifications quand les données changent, quel que soit l'écran qui les modifie
(back-office, espace propriétaire, Django admin…).

- bien publié (statut → DISPONIBLE)  → alertes de recherche correspondantes (« Nouveau bien disponible à Cocody Abatta »)
- prix en baisse                     → utilisateurs qui ont le bien en favori
- visite confirmée par l'équipe      → le visiteur (« Votre visite est confirmée pour samedi à 10h »)
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.crm.infrastructure.models import AlertFrequency, SearchAlert, VisitRequest, VisitRequestStatus
from apps.notifications.application.service import notify
from apps.notifications.domain import kinds
from apps.properties.infrastructure.models import Property, PropertyFavorite, PropertyStatus
from apps.users.infrastructure.models import User


def _remember(sender, instance, fields, **kwargs):
    """Avant l'enregistrement : garde en mémoire les anciennes valeurs pour détecter un changement."""
    old = None
    if instance.pk and not kwargs.get("raw"):
        old = sender.objects.filter(pk=instance.pk).values(*fields).first()
    instance._old_values = old


@receiver(pre_save, sender=Property)
def property_pre_save(sender, instance, **kwargs):
    _remember(sender, instance, ("status", "price"), **kwargs)


@receiver(post_save, sender=Property)
def property_post_save(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    old = getattr(instance, "_old_values", None) or {}
    place = " ".join(x for x in (instance.neighborhood, instance.commune) if x)

    if instance.status == PropertyStatus.DISPONIBLE and old.get("status") != PropertyStatus.DISPONIBLE:
        alerts = SearchAlert.objects.filter(is_active=True, frequency=AlertFrequency.IMMEDIATE).select_related("user")
        for alert in alerts:
            if alert.user_id == instance.owner_id or not alert.matches(instance):
                continue
            sent = notify(
                alert.user,
                kinds.NEW_MATCH,
                f"Nouveau bien disponible à {place}.",
                f"{instance.title} — {instance.price:,.0f} FCFA".replace(",", " "),
                f"/biens/{instance.slug}",
                dedupe_key=f"match:{instance.pk}",
            )
            if sent:
                SearchAlert.objects.filter(pk=alert.pk).update(last_notified_at=timezone.now())

    old_price = old.get("price")
    if old_price is not None and instance.price < old_price and instance.status in (PropertyStatus.DISPONIBLE, PropertyStatus.OPTION):
        for fav in PropertyFavorite.objects.filter(property=instance).select_related("user"):
            notify(
                fav.user,
                kinds.PRICE_DROP,
                f"Prix en baisse : {instance.title}",
                f"{old_price:,.0f} → {instance.price:,.0f} FCFA".replace(",", " "),
                f"/biens/{instance.slug}",
                dedupe_key=f"drop:{instance.pk}:{instance.price:.0f}",
            )


@receiver(pre_save, sender=VisitRequest)
def visit_pre_save(sender, instance, **kwargs):
    _remember(sender, instance, ("status",), **kwargs)


@receiver(post_save, sender=VisitRequest)
def visit_post_save(sender, instance, created, raw=False, **kwargs):
    if raw or created:
        return
    old = (getattr(instance, "_old_values", None) or {}).get("status")
    if instance.status != VisitRequestStatus.CONFIRMEE or old == VisitRequestStatus.CONFIRMEE:
        return
    visitor: User | None = instance.user or instance.lead.user
    when = (
        f"{kinds.DAYS_FR[instance.scheduled_date.weekday()]} à "
        f"{kinds.hour_fr(instance.scheduled_time.hour, instance.scheduled_time.minute)}"
    )
    notify(
        visitor,
        kinds.VISIT_CONFIRMED,
        f"Votre visite est confirmée pour {when}.",
        f"{instance.property.title} ({instance.property.reference})",
        "/espace/demandes",
        dedupe_key=f"visit:{instance.pk}:confirmed",
    )
