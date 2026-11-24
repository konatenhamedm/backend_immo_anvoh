import uuid

from django.conf import settings
from django.db import models

from apps.crm.infrastructure.models import Lead
from apps.notifications.domain.kinds import KIND_CHOICES


class Notification(models.Model):
    """Notification destinée à un utilisateur : affichée dans l'application et envoyée par e-mail."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField("Type", max_length=30, choices=KIND_CHOICES)
    title = models.CharField("Titre", max_length=200)
    body = models.TextField("Message", blank=True)
    url = models.CharField("Lien dans l'application", max_length=300, blank=True)
    # Évite les doublons (ex. même bien annoncé deux fois à la même alerte) : unique par utilisateur.
    dedupe_key = models.CharField(max_length=200, blank=True)
    read_at = models.DateTimeField("Lue le", null=True, blank=True)
    emailed_at = models.DateTimeField("E-mail envoyé le", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "read_at", "-created_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "dedupe_key"], condition=~models.Q(dedupe_key=""), name="uniq_notification_dedupe"
            )
        ]

    def __str__(self):
        return f"{self.get_kind_display()} → {self.user_id}"


class FollowUpStatus(models.TextChoices):
    OUVERTE = "OUVERTE", "À faire"
    FAITE = "FAITE", "Faite"


class FollowUpTask(models.Model):
    """Tâche de relance : prospect sans activité depuis X jours (spécification §28)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="followups")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="followups"
    )
    reason = models.CharField("Motif", max_length=255)
    due_date = models.DateField("À faire pour le")
    status = models.CharField(max_length=10, choices=FollowUpStatus.choices, default=FollowUpStatus.OUVERTE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["due_date", "created_at"]
        indexes = [models.Index(fields=["status", "due_date"])]

    def __str__(self):
        return f"Relance {self.lead_id} ({self.get_status_display()})"
