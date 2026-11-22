from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager personnalisé pour utiliser l'email comme identifiant unique."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class UserRole(models.TextChoices):
    PARTICULIER = "PARTICULIER", "Client Particulier"
    INVESTISSEUR = "INVESTISSEUR", "Investisseur"
    PROPRIETAIRE = "PROPRIETAIRE", "Propriétaire"
    PROMOTEUR = "PROMOTEUR", "Promoteur Immobilier"
    AGENT = "AGENT", "Agent Commercial / Conseiller"
    NOTAIRE = "NOTAIRE", "Notaire partenaire"
    ADMIN = "ADMIN", "Administrateur"


class IdentityStatus(models.TextChoices):
    NON_SOUMIS = "NON_SOUMIS", "Non soumise"
    EN_ATTENTE = "EN_ATTENTE", "En cours de vérification"
    VERIFIE = "VERIFIE", "Identité vérifiée"
    REFUSE = "REFUSE", "Refusée"


# Rôles qu'un visiteur peut choisir lui-même à l'inscription (les autres sont attribués par un administrateur).
SELF_SERVICE_ROLES = (UserRole.PARTICULIER, UserRole.INVESTISSEUR, UserRole.PROPRIETAIRE)


class ProjectObjective(models.TextChoices):
    HABITER = "HABITER", "Habiter (Résidence principale)"
    INVESTIR = "INVESTIR", "Investir (Rendement locatif)"
    LOUER = "LOUER", "Louer"
    AUTRE = "AUTRE", "Autre projet"


class ProjectTimeframe(models.TextChoices):
    IMMEDIAT = "IMMEDIAT", "Immédiatement"
    MOIS_0_3 = "0_3_MOIS", "0 à 3 mois"
    MOIS_3_6 = "3_6_MOIS", "3 à 6 mois"
    MOIS_6_12 = "6_12_MOIS", "6 à 12 mois"
    PLUS_TARD = "PLUS_TARD", "Plus tard"


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé (THIEBBRO IMMO).
    Écran 03 Inscription & Écran 18 Profil Utilisateur.
    """

    username = None
    email = models.EmailField("Adresse email", unique=True)
    phone_number = models.CharField("Téléphone", max_length=30)
    country_of_residence = models.CharField("Pays de résidence", max_length=100, default="Côte d'Ivoire")
    is_diaspora = models.BooleanField("Membre de la diaspora", default=False)
    role = models.CharField("Rôle / Profil", max_length=20, choices=UserRole.choices, default=UserRole.PARTICULIER)

    # Section "Mon projet" (Écran 18 Profil & Écran 10 Questionnaire)
    project_objective = models.CharField(
        "Objectif immobilier", max_length=30, choices=ProjectObjective.choices, blank=True, null=True
    )
    project_budget = models.DecimalField(
        "Budget envisagé (FCFA)", max_digits=14, decimal_places=2, blank=True, null=True
    )
    project_down_payment = models.DecimalField(
        "Apport disponible (FCFA)", max_digits=14, decimal_places=2, blank=True, null=True
    )
    project_zone = models.CharField("Zone souhaitée (ex: Cocody, Bingerville)", max_length=150, blank=True)
    project_timeframe = models.CharField(
        "Délai de réalisation", max_length=30, choices=ProjectTimeframe.choices, blank=True, null=True
    )

    # Paramètres utilisateur
    notifications_enabled = models.BooleanField("Notifications actives", default=True)
    # Préférences détaillées : {"new_matches": bool, "price_drops": bool, "visit_reminders": bool, "newsletter": bool}
    notification_preferences = models.JSONField("Préférences de notification", default=dict, blank=True)

    # Vérification d'identité (KYC) — exigée des propriétaires avant publication, utile pour les souscriptions
    identity_status = models.CharField(
        "Vérification d'identité", max_length=20, choices=IdentityStatus.choices, default=IdentityStatus.NON_SOUMIS
    )
    identity_document = models.FileField("Pièce d'identité", upload_to="kyc/%Y/%m/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number"]

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["-created_at"]

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return f"{full_name or self.email} ({self.get_role_display()})"
