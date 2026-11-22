import uuid

from django.conf import settings
from django.db import models

from apps.properties.infrastructure.models import Property


class Notary(models.Model):
    """Notaire partenaire (étude notariale). Peut être lié à un compte utilisateur de rôle NOTAIRE."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notary_profile",
        verbose_name="Compte utilisateur",
    )
    full_name = models.CharField("Nom (ex: Me Aya Koné)", max_length=150)
    office = models.CharField("Étude / Office notarial", max_length=200)
    city = models.CharField("Commune / Ville", max_length=100)
    phone_number = models.CharField("Téléphone", max_length=30, blank=True)
    email = models.EmailField("Email", blank=True)
    is_active = models.BooleanField("Partenaire actif", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notaire partenaire"
        verbose_name_plural = "Notaires partenaires"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.office})"


class AccreditationStep(models.IntegerChoices):
    DEPOT = 0, "Dépôt des pièces"
    CONTROLE_JURIDIQUE = 1, "Contrôle juridique"
    CADASTRE = 2, "Vérification cadastre"
    CERTIFICATION = 3, "Certification notariale"


class AccreditationStatus(models.TextChoices):
    EN_COURS = "EN_COURS", "En cours"
    CERTIFIE = "CERTIFIE", "Certifié"
    REFUSE = "REFUSE", "Refusé"


class CertificationLevel(models.TextChoices):
    VERIFIE = "VERIFIE", "Bien vérifié"
    VERIFICATION_RENFORCEE = "VERIFICATION_RENFORCEE", "Vérification renforcée"


class AccreditationFile(models.Model):
    """Dossier de vérification notariale d'un bien : condition de sa mise en ligne."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name="accreditation")
    notary = models.ForeignKey(Notary, on_delete=models.SET_NULL, null=True, blank=True, related_name="files")
    step = models.PositiveSmallIntegerField("Étape", choices=AccreditationStep.choices, default=AccreditationStep.DEPOT)
    status = models.CharField(
        "Statut", max_length=20, choices=AccreditationStatus.choices, default=AccreditationStatus.EN_COURS
    )
    certification_level = models.CharField(
        "Niveau de certification", max_length=30, choices=CertificationLevel.choices, blank=True
    )
    refusal_reason = models.TextField("Motif du refus", blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    certified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Dossier d'accréditation"
        verbose_name_plural = "Dossiers d'accréditation"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Accréditation {self.property.reference} — {self.get_step_display()} ({self.get_status_display()})"


class DocumentType(models.TextChoices):
    TITRE = "TITRE", "Titre foncier, ACD ou lettre d'attribution"
    IDENTITE = "IDENTITE", "Pièce d'identité du propriétaire"
    PLAN = "PLAN", "Plan cadastral / extrait topographique"
    FISCAL = "FISCAL", "Attestation de situation fiscale"


REQUIRED_DOCUMENTS = (DocumentType.TITRE, DocumentType.IDENTITE, DocumentType.PLAN)


class DocumentStatus(models.TextChoices):
    DEPOSE = "DEPOSE", "Déposé"
    VALIDE = "VALIDE", "Validé"
    REJETE = "REJETE", "Rejeté"


class PropertyDocument(models.Model):
    """Pièce justificative déposée par le propriétaire pour l'accréditation d'un bien."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField("Type de pièce", max_length=20, choices=DocumentType.choices)
    file = models.FileField("Fichier", upload_to="documents/%Y/%m/")
    status = models.CharField("Statut", max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DEPOSE)
    comment = models.CharField("Commentaire du vérificateur", max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pièce justificative"
        verbose_name_plural = "Pièces justificatives"
        ordering = ["doc_type", "-uploaded_at"]

    def __str__(self):
        return f"{self.get_doc_type_display()} — {self.property.reference}"
