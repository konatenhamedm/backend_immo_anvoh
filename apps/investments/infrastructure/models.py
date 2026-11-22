import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class PlanRisk(models.TextChoices):
    FAIBLE = "FAIBLE", "Faible"
    MODERE = "MODERE", "Modéré"
    DYNAMIQUE = "DYNAMIQUE", "Dynamique"


class PlanStatus(models.TextChoices):
    BROUILLON = "BROUILLON", "Brouillon"
    OUVERT = "OUVERT", "Ouvert"
    COMPLET = "COMPLET", "Complet"
    FERME = "FERME", "Fermé"


class InvestmentPlan(models.Model):
    """Formule d'investissement proposée (Plan Patrimoine, Rendement locatif, Diaspora…)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField("Code (URL)", max_length=50, unique=True)
    name = models.CharField("Nom", max_length=120)
    tagline = models.CharField("Accroche", max_length=255, blank=True)
    description = models.TextField("Description", blank=True)
    min_ticket = models.DecimalField("Ticket minimum (FCFA)", max_digits=14, decimal_places=2)
    duration_label = models.CharField("Durée (ex: 5 à 10 ans)", max_length=100, blank=True)
    target_yield_label = models.CharField("Rendement cible (ex: 8 à 12 % brut / an)", max_length=120, blank=True)
    risk = models.CharField("Niveau de risque", max_length=20, choices=PlanRisk.choices, default=PlanRisk.MODERE)
    features = models.JSONField("Points forts", default=list, blank=True)
    allows_instalments = models.BooleanField("Paiement échelonné possible", default=False)
    highlight = models.BooleanField("Mis en avant", default=False)
    status = models.CharField("Statut", max_length=20, choices=PlanStatus.choices, default=PlanStatus.OUVERT)
    order = models.PositiveSmallIntegerField("Ordre d'affichage", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Plan d'investissement"
        verbose_name_plural = "Plans d'investissement"
        ordering = ["order", "min_ticket"]

    def __str__(self):
        return self.name


class PaymentMethod(models.TextChoices):
    ORANGE = "ORANGE", "Orange Money"
    MTN = "MTN", "MTN MoMo"
    WAVE = "WAVE", "Wave"
    CARD = "CARD", "Carte bancaire"
    TRANSFER = "TRANSFER", "Virement bancaire"


MOBILE_MONEY = (PaymentMethod.ORANGE, PaymentMethod.MTN, PaymentMethod.WAVE)


class SubscriptionStatus(models.TextChoices):
    EN_ATTENTE = "EN_ATTENTE", "En attente du premier versement"
    ACTIVE = "ACTIVE", "Actif"
    TERMINEE = "TERMINEE", "Terminé"
    ANNULEE = "ANNULEE", "Annulé"


class Subscription(models.Model):
    """Souscription d'un client à un plan. Les fonds transitent par le compte séquestre du notaire."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField("Référence", max_length=30, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="subscriptions")
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.PROTECT, related_name="subscriptions")
    asset_label = models.CharField("Actif affecté (ex: Lot 500 m² — Songon)", max_length=200, blank=True)
    amount = models.DecimalField("Montant souscrit (FCFA)", max_digits=14, decimal_places=2)
    months = models.PositiveSmallIntegerField("Nombre de mensualités", null=True, blank=True)
    payment_method = models.CharField("Moyen de paiement", max_length=20, choices=PaymentMethod.choices)
    payment_phone = models.CharField("Numéro mobile money", max_length=30, blank=True)
    estimated_value = models.DecimalField(
        "Valeur estimée (FCFA)", max_digits=14, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        "Statut", max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.EN_ATTENTE
    )
    accepted_terms_at = models.DateTimeField("Notice acceptée le")
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Souscription"
        verbose_name_plural = "Souscriptions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.reference} — {self.plan.name} ({self.amount:,.0f} FCFA)"

    def save(self, *args, **kwargs):
        if not self.reference:
            prefix = f"SUB-{timezone.now():%Y}-"
            count = Subscription.objects.filter(reference__startswith=prefix).count() + 1
            self.reference = f"{prefix}{count:04d}"
        super().save(*args, **kwargs)


class EntryKind(models.TextChoices):
    VERSEMENT = "VERSEMENT", "Versement"
    MENSUALITE = "MENSUALITE", "Mensualité"
    REVENU = "REVENU", "Revenu reversé"


class EntryStatus(models.TextChoices):
    A_VENIR = "A_VENIR", "À venir"
    EN_VALIDATION = "EN_VALIDATION", "En attente de validation"
    PAYE = "PAYE", "Payé"
    PROGRAMME = "PROGRAMME", "Programmé"
    RECU = "RECU", "Reçu"
    ECHEC = "ECHEC", "Échec"


class ScheduleEntry(models.Model):
    """Ligne d'échéancier : versement ou mensualité dus par le client, ou revenu qui lui est reversé."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="entries")
    kind = models.CharField("Nature", max_length=20, choices=EntryKind.choices)
    label = models.CharField("Libellé", max_length=200)
    due_date = models.DateField("Échéance")
    amount = models.DecimalField("Montant (FCFA)", max_digits=14, decimal_places=2)
    status = models.CharField("Statut", max_length=20, choices=EntryStatus.choices, default=EntryStatus.A_VENIR)
    payment_reference = models.CharField("Référence de paiement", max_length=80, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Ligne d'échéancier"
        verbose_name_plural = "Échéancier"
        ordering = ["-due_date"]
        indexes = [
            models.Index(fields=["status", "due_date"]),
        ]

    @property
    def is_income(self) -> bool:
        return self.kind == EntryKind.REVENU


class InvestmentDocument(models.Model):
    """Contrat, attestation de séquestre, relevés… mis à disposition du souscripteur."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField("Titre", max_length=200)
    file = models.FileField("Fichier", upload_to="investments/%Y/%m/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
