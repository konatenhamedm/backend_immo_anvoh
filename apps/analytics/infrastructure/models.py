import uuid

from django.conf import settings
from django.db import models

from apps.crm.infrastructure.models import AcquisitionChannel


class AnalyticsEvent(models.Model):
    """Un événement de mesure d'audience ou de conversion. Aucune donnée personnelle (ni e-mail, ni téléphone)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Événement", max_length=40)
    occurred_at = models.DateTimeField("Date", auto_now_add=True)
    # Identifiant aléatoire du navigateur (pas une personne) : compte les utilisateurs actifs sans les identifier.
    anonymous_id = models.CharField(max_length=64, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="analytics_events"
    )
    channel = models.CharField("Canal", max_length=20, blank=True, choices=AcquisitionChannel.choices)
    path = models.CharField(max_length=200, blank=True)
    properties = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["name", "occurred_at"]),
            models.Index(fields=["anonymous_id", "occurred_at"]),
        ]
        verbose_name = "Événement"
        verbose_name_plural = "Événements"

    def __str__(self):
        return f"{self.name} {self.occurred_at:%Y-%m-%d %H:%M}"


class ChannelSpend(models.Model):
    """Dépense marketing d'un canal pour un mois : nécessaire au calcul du ROI par canal (spécification §29)."""

    channel = models.CharField("Canal", max_length=20, choices=AcquisitionChannel.choices)
    month = models.DateField("Mois (1er jour)", help_text="Saisir le 1er du mois, ex. 2026-11-01")
    amount = models.DecimalField("Dépense (FCFA)", max_digits=14, decimal_places=2)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["channel", "month"], name="uniq_spend_channel_month")]
        ordering = ["-month", "channel"]
        verbose_name = "Dépense marketing"
        verbose_name_plural = "Dépenses marketing"

    def __str__(self):
        return f"{self.get_channel_display()} {self.month:%m/%Y} : {self.amount}"
