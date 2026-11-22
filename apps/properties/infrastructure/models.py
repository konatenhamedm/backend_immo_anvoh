import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class PropertyType(models.TextChoices):
    APPARTEMENT = "APPARTEMENT", "Appartement"
    VILLA = "VILLA", "Villa"
    MAISON = "MAISON", "Maison"
    DUPLEX = "DUPLEX", "Duplex"
    TERRAIN = "TERRAIN", "Terrain"
    IMMEUBLE = "IMMEUBLE", "Immeuble de rapport"
    RESIDENCE_MEUBLEE = "RESIDENCE_MEUBLEE", "Résidence meublée"
    BUREAU = "BUREAU", "Bureau"
    COMMERCIAL = "COMMERCIAL", "Local commercial"


class PropertyTypology(models.TextChoices):
    F1 = "F1", "F1 / Studio"
    F2 = "F2", "F2 (2 pièces)"
    F3 = "F3", "F3 (3 pièces)"
    F4 = "F4", "F4 (4 pièces)"
    F5 = "F5", "F5 (5 pièces et plus)"
    AUTRE = "AUTRE", "Autre configuration"


class PropertyGoal(models.TextChoices):
    HABITATION = "HABITATION", "Habitation / Résidence"
    INVESTISSEMENT = "INVESTISSEMENT", "Investissement locatif"
    MIXTE = "MIXTE", "Investissement / Habitation"
    LOCATION = "LOCATION", "Location"


class PropertyStatus(models.TextChoices):
    BROUILLON = "BROUILLON", "Brouillon"
    EN_ATTENTE = "EN_ATTENTE", "En attente de validation"
    DISPONIBLE = "DISPONIBLE", "Publié / Disponible"
    OPTION = "OPTION", "Option posée"
    RESERVE = "RESERVE", "Réservé"
    VENDU = "VENDU", "Vendu"
    ARCHIVE = "ARCHIVE", "Archivé"


class VerificationStatus(models.TextChoices):
    NON_VERIFIE = "NON_VERIFIE", "Non vérifié"
    EN_ATTENTE = "EN_ATTENTE", "En attente de vérification"
    VERIFIE = "VERIFIE", "Bien vérifié (Documents certifiés)"
    VERIFICATION_RENFORCEE = "VERIFICATION_RENFORCEE", "Vérification renforcée (Titre foncier / ACD vérifié)"
    REFUSE = "REFUSE", "Refusé (pièces non conformes)"


class TransactionType(models.TextChoices):
    VENTE = "VENTE", "Vente"
    LOCATION = "LOCATION", "Location"


class TitleDeedType(models.TextChoices):
    TITRE_FONCIER = "TITRE_FONCIER", "Titre Foncier"
    ACD = "ACD", "ACD"
    LETTRE_ATTRIBUTION = "LETTRE_ATTRIBUTION", "Lettre d'attribution"
    CERTIFICAT_PROPRIETE = "CERTIFICAT_PROPRIETE", "Certificat de propriété"


# Statuts visibles par le public (catalogue, fiche, favoris).
PUBLIC_STATUSES = ("DISPONIBLE", "OPTION", "RESERVE")


def unique_slug(instance, base: str, max_length: int = 250) -> str:
    """Slug unique pour le modèle de `instance` (suffixe -2, -3… en cas de collision)."""
    root = slugify(base)[:max_length] or "bien"
    candidate, n = root, 2
    model = type(instance)
    while model.objects.filter(slug=candidate).exclude(pk=instance.pk).exists():
        candidate = f"{root[: max_length - 6]}-{n}"
        n += 1
    return candidate


class DevelopmentProject(models.Model):
    """
    Programmes immobiliers neufs (Écran 04, 13, 20 et 24).
    Exemple : Projet L'ÉTOILE (100 lots).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Nom du programme", max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    developer_name = models.CharField("Promoteur immobilier", max_length=150)
    city = models.CharField("Ville", max_length=100, default="Abidjan")
    commune = models.CharField("Commune", max_length=100)
    neighborhood = models.CharField("Quartier", max_length=100)
    description = models.TextField("Présentation du projet")

    total_lots_count = models.PositiveIntegerField("Nombre total de logements / lots", default=1)
    delivery_date = models.CharField("Calendrier de livraison (ex: T4 2026)", max_length=100, blank=True)
    starting_price = models.DecimalField("Prix à partir de (FCFA)", max_digits=14, decimal_places=2)

    cover_image = models.ImageField("Image principale", upload_to="projects/covers/", blank=True, null=True)
    cover_image_url = models.URLField("Image principale (URL externe)", max_length=500, blank=True)
    brochure_pdf = models.FileField("Brochure / Documents PDF", upload_to="projects/docs/", blank=True, null=True)
    virtual_tour_url = models.URLField("Visite virtuelle 3D", blank=True, null=True)
    construction_progress = models.PositiveSmallIntegerField("Avancement du chantier (%)", default=0)

    is_featured = models.BooleanField("Mettre en avant sur l'accueil", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Programme immobilier neuf"
        verbose_name_plural = "Programmes immobiliers neufs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.commune} ({self.developer_name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, 190)
        super().save(*args, **kwargs)


class ProjectLot(models.Model):
    """
    Lots d'un programme immobilier (Écran 20 et 24).
    Ex: Lot 101, F3, 85m², 100M FCFA, Disponible.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(DevelopmentProject, on_delete=models.CASCADE, related_name="lots")
    lot_number = models.CharField("Numéro / Référence de lot (ex: Lot 101)", max_length=50)
    typology = models.CharField(
        "Typologie", max_length=20, choices=PropertyTypology.choices, default=PropertyTypology.F3
    )
    building_name = models.CharField("Bâtiment / Tour", max_length=50, blank=True)
    floor = models.IntegerField("Étage", default=0)
    surface_sqm = models.DecimalField("Superficie (m²)", max_digits=8, decimal_places=2)
    price = models.DecimalField("Prix (FCFA)", max_digits=14, decimal_places=2)
    status = models.CharField(
        "Disponibilité du lot", max_length=20, choices=PropertyStatus.choices, default=PropertyStatus.DISPONIBLE
    )

    class Meta:
        verbose_name = "Lot de programme"
        verbose_name_plural = "Lots de programmes"
        ordering = ["lot_number"]

    def __str__(self):
        return f"{self.project.name} - {self.lot_number} ({self.get_typology_display()})"


class Property(models.Model):
    """
    Modèle central Bien Immobilier.
    Couvre les Écrans 04 (Accueil), 05 (Recherche), 06 (Résultats), 07 (Fiche bien), 13 (Investir).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField("Référence unique (ex: THI-2026-001)", max_length=50, unique=True, blank=True)
    title = models.CharField("Titre du bien", max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField("Description détaillée")

    property_type = models.CharField("Type de bien", max_length=30, choices=PropertyType.choices)
    transaction = models.CharField(
        "Transaction", max_length=10, choices=TransactionType.choices, default=TransactionType.VENTE
    )
    title_deed = models.CharField(
        "Type de titre de propriété", max_length=30, choices=TitleDeedType.choices, blank=True
    )
    typology = models.CharField(
        "Typologie", max_length=20, choices=PropertyTypology.choices, default=PropertyTypology.F3
    )
    target_goal = models.CharField(
        "Objectif cible", max_length=20, choices=PropertyGoal.choices, default=PropertyGoal.MIXTE
    )

    status = models.CharField(
        "Statut", max_length=20, choices=PropertyStatus.choices, default=PropertyStatus.DISPONIBLE
    )
    verification_status = models.CharField(
        "Badge de vérification",
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.EN_ATTENTE,
    )

    # Flags éditoriaux pour l'accueil & Espace Investir
    is_featured = models.BooleanField("Opportunité du moment (Accueil)", default=False)
    is_selected_investment = models.BooleanField("Investissement sélectionné (Accueil & Investir)", default=False)

    # Finances en FCFA
    price = models.DecimalField("Prix (FCFA)", max_digits=14, decimal_places=2)
    recommended_down_payment = models.DecimalField(
        "Apport recommandé (FCFA)", max_digits=14, decimal_places=2, null=True, blank=True
    )
    estimated_monthly_rent = models.DecimalField(
        "Loyer estimatif mensuel (FCFA)", max_digits=12, decimal_places=2, null=True, blank=True
    )
    estimated_yield_rate = models.DecimalField(
        "Rentabilité brute estimative (%)", max_digits=5, decimal_places=2, null=True, blank=True
    )
    investment_score = models.PositiveIntegerField("Indice / Score THIEBBRO (0-100)", default=75)

    # Localisation précise
    city = models.CharField("Ville", max_length=100, default="Abidjan")
    commune = models.CharField("Commune (Cocody, Bingerville, etc.)", max_length=100)
    neighborhood = models.CharField("Quartier (Abatta, Angré, etc.)", max_length=100)
    address = models.CharField("Adresse / Repère géographique", max_length=255, blank=True)
    latitude = models.DecimalField("Latitude GPS", max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField("Longitude GPS", max_digits=9, decimal_places=6, null=True, blank=True)

    # Spécifications physiques
    surface_sqm = models.DecimalField("Superficie (m²)", max_digits=8, decimal_places=2)
    rooms_count = models.PositiveIntegerField("Nombre total de pièces", default=3)
    bedrooms_count = models.PositiveIntegerField("Chambres", default=2)
    bathrooms_count = models.PositiveIntegerField("Salles de bains / eau", default=2)

    # Équipements & Commodités
    has_parking = models.BooleanField("Parking", default=False)
    has_swimming_pool = models.BooleanField("Piscine", default=False)
    has_elevator = models.BooleanField("Ascenseur", default=False)
    has_security = models.BooleanField("Sécurité 24/7", default=False)
    has_generator = models.BooleanField("Groupe électrogène", default=False)
    has_green_space = models.BooleanField("Espace vert", default=False)
    amenities_extra = models.JSONField("Autres équipements (liste libre)", default=list, blank=True)

    # Médias & Visites
    video_url = models.URLField("Vidéo / Drone", blank=True, null=True)
    virtual_tour_url = models.URLField("Visite 3D virtuelle", blank=True, null=True)
    tour_scan_requested = models.BooleanField("Scan Matterport demandé", default=False)
    tour_scan_scheduled_at = models.DateTimeField("Scan Matterport planifié le", null=True, blank=True)
    tour_scan_technician = models.CharField("Technicien 3D", max_length=120, blank=True)

    # Audience (compteur incrémenté à chaque consultation publique de la fiche)
    views_count = models.PositiveIntegerField("Nombre de vues", default=0)

    # Relations
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="properties_owned",
        verbose_name="Propriétaire (annonceur)",
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="properties_managed",
        verbose_name="Conseiller / Agent responsable",
    )
    development_project = models.ForeignKey(
        DevelopmentProject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="properties",
        verbose_name="Rattaché au Programme",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bien immobilier"
        verbose_name_plural = "Biens immobiliers"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["commune"]),
            models.Index(fields=["property_type"]),
            models.Index(fields=["verification_status"]),
        ]

    def __str__(self):
        return f"[{self.reference}] {self.title} - {self.commune} ({self.price:,.0f} FCFA)"

    @property
    def is_public(self) -> bool:
        return self.status in PUBLIC_STATUSES

    def save(self, *args, **kwargs):
        if not self.reference:
            year = timezone.now().year
            prefix = f"THI-{year}-"
            last = (
                Property.objects.filter(reference__startswith=prefix)
                .order_by("-reference")
                .values_list("reference", flat=True)
                .first()
            )
            seq = int(last.rsplit("-", 1)[-1]) + 1 if last and last.rsplit("-", 1)[-1].isdigit() else 1
            self.reference = f"{prefix}{seq:03d}"
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)


class PropertyImage(models.Model):
    """Galerie photos d'un bien (Écran 07 Haut de page). Fichier envoyé OU URL externe (CDN, banque d'images)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="properties/%Y/%m/", blank=True, null=True)
    external_url = models.URLField("URL externe", max_length=500, blank=True)
    caption = models.CharField("Légende", max_length=150, blank=True)
    is_cover = models.BooleanField("Photo de couverture", default=False)
    order = models.PositiveIntegerField("Ordre d'affichage", default=0)

    class Meta:
        ordering = ["order", "id"]

    def url(self, request=None):
        if self.image:
            return request.build_absolute_uri(self.image.url) if request else self.image.url
        return self.external_url or None


class PropertyFavorite(models.Model):
    """Favoris de l'utilisateur (Écran 14)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "property")
        ordering = ["-created_at"]
        verbose_name = "Favori"
        verbose_name_plural = "Favoris"
