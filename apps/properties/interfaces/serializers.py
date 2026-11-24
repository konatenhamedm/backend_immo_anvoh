from django.core.exceptions import ObjectDoesNotExist
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.properties.domain.images import MAX_UPLOAD_BYTES
from apps.properties.infrastructure.models import (
    DevelopmentProject,
    ProjectDocument,
    ProjectLot,
    Property,
    PropertyFavorite,
    PropertyImage,
    PropertyStatus,
)
from apps.users.interfaces.permissions import is_staff_or_agent

# Équipements booléens → libellés affichés (complétés par la liste libre `amenities_extra`).
AMENITY_FLAGS = [
    ("has_security", "Gardiennage 24/7"),
    ("has_generator", "Groupe électrogène"),
    ("has_parking", "Parking"),
    ("has_swimming_pool", "Piscine"),
    ("has_elevator", "Ascenseur"),
    ("has_green_space", "Jardin / Espace vert"),
]


PUBLIC_COORDINATE_DIGITS = 2  # ≈ 1,1 km : le site promet « adresse exacte communiquée après rendez-vous »


def _coordinate(serializer, obj, value):
    """Position publique arrondie à environ 1 km ; position exacte seulement pour l'équipe et le propriétaire du bien."""
    if value is None:
        return None
    request = serializer.context.get("request")
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and (is_staff_or_agent(user) or obj.owner_id == user.id):
        return float(value)
    return round(float(value), PUBLIC_COORDINATE_DIGITS)


def _images(obj):
    # S'appuie sur le prefetch `images` (pas de requête par bien).
    return sorted(obj.images.all(), key=lambda i: (not i.is_cover, i.order))


def _accreditation(obj):
    """Dossier d'accréditation du bien, ou None (relation inverse OneToOne absente)."""
    try:
        return obj.accreditation
    except ObjectDoesNotExist:
        return None


def _is_favorited(serializer, obj) -> bool:
    ids = serializer.context.get("favorite_ids")
    if ids is not None:
        return obj.id in ids
    request = serializer.context.get("request")
    user = request.user if request else None
    if user and user.is_authenticated:
        return obj.favorited_by.filter(user=user).exists()
    return False


def favorite_ids_for(request):
    """Ids des favoris de l'utilisateur, à passer dans le contexte pour éviter une requête par carte."""
    if request and request.user.is_authenticated:
        return set(PropertyFavorite.objects.filter(user=request.user).values_list("property_id", flat=True))
    return set()


class PropertyImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyImage
        fields = ["id", "url", "thumbnail_url", "caption", "is_cover", "order"]

    @extend_schema_field({"type": "string", "format": "uri", "nullable": True})
    def get_thumbnail_url(self, obj):
        return obj.thumbnail_url(self.context.get("request"))

    @extend_schema_field({"type": "string", "format": "uri", "nullable": True})
    def get_url(self, obj):
        return obj.url(self.context.get("request"))


class ProjectLotSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    typology_display = serializers.CharField(source="get_typology_display", read_only=True)

    class Meta:
        model = ProjectLot
        fields = [
            "id",
            "lot_number",
            "typology",
            "typology_display",
            "building_name",
            "floor",
            "surface_sqm",
            "price",
            "status",
            "status_display",
        ]


class ProjectDocumentSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    url = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    format = serializers.SerializerMethodField()

    class Meta:
        model = ProjectDocument
        fields = ["id", "kind", "kind_display", "title", "url", "size", "format", "created_at"]
        read_only_fields = fields

    @extend_schema_field({"type": "string", "format": "uri"})
    def get_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url

    def get_size(self, obj) -> int | None:
        try:
            return obj.file.size
        except (OSError, ValueError):
            return None

    def get_format(self, obj) -> str:
        return obj.file.name.rsplit(".", 1)[-1].lower() if "." in obj.file.name else ""


class ProjectDocumentUploadSerializer(serializers.Serializer):
    ALLOWED = {"pdf", "jpg", "jpeg", "png", "webp"}
    MAX_BYTES = 20 * 1024 * 1024

    kind = serializers.ChoiceField(choices=ProjectDocument._meta.get_field("kind").choices, default="DOCUMENT")
    title = serializers.CharField(max_length=150)
    file = serializers.FileField()

    def validate_file(self, f):
        ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
        if ext not in self.ALLOWED:
            raise serializers.ValidationError("Format accepté : PDF, JPG, PNG ou WebP.")
        if f.size > self.MAX_BYTES:
            raise serializers.ValidationError("Fichier trop lourd (20 Mo au maximum).")
        return f


class PaymentStepSerializer(serializers.Serializer):
    """Une étape de l'échéancier : « Réservation : 10 % »."""

    label = serializers.CharField(max_length=80)
    percent = serializers.FloatField(min_value=0, max_value=100)


class ProjectCoverMixin:
    """Image de couverture d'un programme : fichier téléversé, sinon URL externe, sinon rien."""

    @extend_schema_field({"type": "string", "format": "uri", "nullable": True})
    def get_cover(self, obj):
        if obj.cover_image:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.cover_image.url) if request else obj.cover_image.url
        return obj.cover_image_url or None


class DevelopmentProjectSerializer(ProjectCoverMixin, serializers.ModelSerializer):
    """Programme complet, avec la liste de ses lots (administration des programmes, fiche d'un programme)."""

    lots = ProjectLotSerializer(many=True, read_only=True)
    documents = ProjectDocumentSerializer(many=True, read_only=True)
    payment_schedule = PaymentStepSerializer(many=True, required=False)
    cover = serializers.SerializerMethodField()
    lots_sold = serializers.SerializerMethodField()

    def validate_payment_schedule(self, steps):
        if sum(s["percent"] for s in steps) > 100.0001:
            raise serializers.ValidationError("L'échéancier ne peut pas dépasser 100 %.")
        return steps

    class Meta:
        model = DevelopmentProject
        fields = [
            "id",
            "name",
            "slug",
            "developer_name",
            "city",
            "commune",
            "neighborhood",
            "description",
            "total_lots_count",
            "lots_sold",
            "delivery_date",
            "starting_price",
            "cover_image",
            "cover_image_url",
            "cover",
            "brochure_pdf",
            "virtual_tour_url",
            "construction_progress",
            "payment_schedule",
            "payment_notes",
            "is_featured",
            "lots",
            "documents",
        ]
        read_only_fields = ["slug"]

    def get_lots_sold(self, obj) -> int:
        return sum(1 for lot in obj.lots.all() if lot.status == PropertyStatus.VENDU)


class DevelopmentProjectSummarySerializer(ProjectCoverMixin, serializers.ModelSerializer):
    """
    Programme SANS la liste de ses lots, pour les écrans qui ne les affichent pas (accueil, « Investir »).

    Les décomptes `lots_sold` / `lots_available` viennent de la base (annotations de `project_summaries()` dans
    views/_common.py) : une seule requête au lieu de charger chaque lot. Un programme de 120 lots pèse ~300 octets
    ici contre ~30 Ko avec DevelopmentProjectSerializer.
    """

    cover = serializers.SerializerMethodField()
    lots_sold = serializers.IntegerField(read_only=True)
    lots_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = DevelopmentProject
        fields = [
            "id",
            "name",
            "slug",
            "developer_name",
            "city",
            "commune",
            "neighborhood",
            "total_lots_count",
            "lots_sold",
            "lots_available",
            "delivery_date",
            "starting_price",
            "cover",
            "construction_progress",
            "is_featured",
        ]
        read_only_fields = fields


class PropertyCardSerializer(serializers.ModelSerializer):
    """
    Carte de bien (accueil, résultats, investir, favoris, listes back-office).
    Contient tout ce qu'affichent les cartes du site : photos, badges, rendement, score, audience.
    """

    cover_image = serializers.SerializerMethodField()
    cover_thumb = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    image_urls = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    property_type_display = serializers.CharField(source="get_property_type_display", read_only=True)
    typology_display = serializers.CharField(source="get_typology_display", read_only=True)
    target_goal_display = serializers.CharField(source="get_target_goal_display", read_only=True)
    title_deed_display = serializers.CharField(source="get_title_deed_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    has_virtual_tour = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    notary_name = serializers.SerializerMethodField()
    leads_count = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "reference",
            "title",
            "slug",
            "property_type",
            "property_type_display",
            "transaction",
            "title_deed",
            "title_deed_display",
            "typology",
            "typology_display",
            "target_goal",
            "target_goal_display",
            "status",
            "status_display",
            "verification_status",
            "price",
            "surface_sqm",
            "rooms_count",
            "bedrooms_count",
            "bathrooms_count",
            "commune",
            "neighborhood",
            "estimated_monthly_rent",
            "estimated_yield_rate",
            "recommended_down_payment",
            "investment_score",
            "cover_image",
            "cover_thumb",
            "latitude",
            "longitude",
            "distance_km",
            "image_urls",
            "is_favorited",
            "has_virtual_tour",
            "amenities",
            "is_featured",
            "is_selected_investment",
            "views_count",
            "leads_count",
            "owner_name",
            "notary_name",
            "tour_scan_requested",
            "tour_scan_scheduled_at",
            "tour_scan_technician",
            "created_at",
        ]

    @extend_schema_field({"type": "string", "format": "uri", "nullable": True})
    def get_cover_image(self, obj):
        imgs = _images(obj)
        return imgs[0].url(self.context.get("request")) if imgs else None

    @extend_schema_field({"type": "number", "nullable": True})
    def get_latitude(self, obj):
        return _coordinate(self, obj, obj.latitude)

    @extend_schema_field({"type": "number", "nullable": True})
    def get_longitude(self, obj):
        return _coordinate(self, obj, obj.longitude)

    @extend_schema_field({"type": "number", "nullable": True})
    def get_distance_km(self, obj):
        # Renseigné uniquement quand la recherche est géographique (lat, lng, radius_km).
        d = getattr(obj, "distance_km", None)
        return round(float(d), 1) if d is not None else None

    @extend_schema_field({"type": "string", "format": "uri", "nullable": True})
    def get_cover_thumb(self, obj):
        imgs = _images(obj)
        return imgs[0].thumbnail_url(self.context.get("request")) if imgs else None

    @extend_schema_field({"type": "array", "items": {"type": "string", "format": "uri"}})
    def get_image_urls(self, obj):
        request = self.context.get("request")
        return [u for u in (img.url(request) for img in _images(obj)) if u]

    def get_is_favorited(self, obj) -> bool:
        return _is_favorited(self, obj)

    def get_has_virtual_tour(self, obj) -> bool:
        return bool(obj.virtual_tour_url)

    def get_amenities(self, obj) -> list[str]:
        return [label for field, label in AMENITY_FLAGS if getattr(obj, field)] + list(obj.amenities_extra or [])

    @extend_schema_field({"type": "string", "nullable": True})
    def get_owner_name(self, obj):
        return f"{obj.owner.first_name} {obj.owner.last_name}".strip() if obj.owner_id and obj.owner else None

    @extend_schema_field({"type": "string", "nullable": True})
    def get_notary_name(self, obj):
        file = _accreditation(obj)
        return file.notary.full_name if file and file.notary_id else None

    @extend_schema_field({"type": "integer", "nullable": True})
    def get_leads_count(self, obj):
        # Renseigné uniquement quand la vue annote le queryset (listes propriétaire / back-office).
        return getattr(obj, "leads_count", None)


class PropertyDetailSerializer(PropertyCardSerializer):
    """Fiche détaillée (Écran 07) : galerie, description, équipements, bloc investissement, visite 3D."""

    images = PropertyImageSerializer(many=True, read_only=True)
    verification_status_display = serializers.CharField(source="get_verification_status_display", read_only=True)
    development_project = serializers.SerializerMethodField()
    accreditation = serializers.SerializerMethodField()
    agent_name = serializers.SerializerMethodField()
    amenities_extra = serializers.ListField(child=serializers.CharField(max_length=100), required=False)

    class Meta(PropertyCardSerializer.Meta):
        fields = PropertyCardSerializer.Meta.fields + [
            "description",
            "city",
            "has_parking",
            "has_swimming_pool",
            "has_elevator",
            "has_security",
            "has_generator",
            "has_green_space",
            "amenities_extra",
            "video_url",
            "virtual_tour_url",
            "tour_scan_requested",
            "tour_scan_scheduled_at",
            "tour_scan_technician",
            "images",
            "verification_status_display",
            "development_project",
            "accreditation",
            "agent_name",
            "updated_at",
        ]

    @extend_schema_field(
        {
            "type": "object",
            "nullable": True,
            "properties": {"id": {"type": "string"}, "name": {"type": "string"}, "slug": {"type": "string"}},
        }
    )
    def get_development_project(self, obj):
        p = obj.development_project
        return {"id": str(p.id), "name": p.name, "slug": p.slug} if p else None

    @extend_schema_field(
        {
            "type": "object",
            "nullable": True,
            "properties": {
                "step": {"type": "integer"},
                "step_label": {"type": "string"},
                "status": {"type": "string"},
                "notary": {"type": "string", "nullable": True},
                "notary_office": {"type": "string", "nullable": True},
                "certified_at": {"type": "string", "format": "date-time", "nullable": True},
            },
        }
    )
    def get_accreditation(self, obj):
        file = _accreditation(obj)
        if not file:
            return None
        return {
            "step": file.step,
            "step_label": file.get_step_display(),
            "status": file.status,
            "notary": file.notary.full_name if file.notary else None,
            "notary_office": file.notary.office if file.notary else None,
            "certified_at": file.certified_at,
        }

    @extend_schema_field({"type": "string", "nullable": True})
    def get_agent_name(self, obj):
        a = obj.assigned_agent
        return f"{a.first_name} {a.last_name}".strip() if a else None


class PropertyWriteSerializer(serializers.ModelSerializer):
    """Création / modification d'un bien (propriétaire ou équipe). Les photos externes passent par `image_urls`."""

    image_urls = serializers.ListField(child=serializers.URLField(max_length=500), required=False, write_only=True)
    amenities_extra = serializers.ListField(child=serializers.CharField(max_length=100), required=False)

    class Meta:
        model = Property
        fields = [
            "id",
            "reference",
            "slug",
            "title",
            "description",
            "property_type",
            "transaction",
            "title_deed",
            "typology",
            "target_goal",
            "price",
            "recommended_down_payment",
            "estimated_monthly_rent",
            "estimated_yield_rate",
            "city",
            "commune",
            "neighborhood",
            "address",
            "latitude",
            "longitude",
            "surface_sqm",
            "rooms_count",
            "bedrooms_count",
            "bathrooms_count",
            "has_parking",
            "has_swimming_pool",
            "has_elevator",
            "has_security",
            "has_generator",
            "has_green_space",
            "amenities_extra",
            "video_url",
            "virtual_tour_url",
            "tour_scan_requested",
            "image_urls",
        ]
        read_only_fields = ["id", "reference", "slug"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Le prix doit être positif.")
        return value

    def _sync_images(self, prop, urls):
        if urls is None:
            return
        prop.images.filter(image="").delete()
        prop.images.filter(image__isnull=True).delete()
        PropertyImage.objects.bulk_create(
            [PropertyImage(property=prop, external_url=u, is_cover=(i == 0), order=i) for i, u in enumerate(urls)]
        )

    def create(self, validated_data):
        urls = validated_data.pop("image_urls", None)
        prop = super().create(validated_data)
        self._sync_images(prop, urls)
        return prop

    def update(self, instance, validated_data):
        urls = validated_data.pop("image_urls", None)
        prop = super().update(instance, validated_data)
        self._sync_images(prop, urls)
        return prop


class PropertyAdminWriteSerializer(PropertyWriteSerializer):
    """L'équipe peut en plus gérer le statut, la mise en avant, le score, l'agent, le propriétaire et le programme."""

    class Meta(PropertyWriteSerializer.Meta):
        fields = PropertyWriteSerializer.Meta.fields + [
            "status",
            "verification_status",
            "is_featured",
            "is_selected_investment",
            "investment_score",
            "assigned_agent",
            "owner",
            "development_project",
            "tour_scan_scheduled_at",
            "tour_scan_technician",
        ]


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(required=False)
    external_url = serializers.URLField(required=False, max_length=500)
    caption = serializers.CharField(required=False, allow_blank=True, max_length=150)
    is_cover = serializers.BooleanField(required=False, default=False)

    def validate_image(self, f):
        if f.size > MAX_UPLOAD_BYTES:
            raise serializers.ValidationError("Photo trop lourde (15 Mo au maximum).")
        return f

    def validate(self, data):
        if not data.get("image") and not data.get("external_url"):
            raise serializers.ValidationError("Envoyez un fichier image ou une URL.")
        return data


class HomeScreenResponseSerializer(serializers.Serializer):
    """Structure de réponse globale pour l'Écran 04 (Accueil)."""

    featured_opportunities = PropertyCardSerializer(many=True)
    recent_properties = PropertyCardSerializer(many=True)
    development_projects = DevelopmentProjectSummarySerializer(many=True)
    selected_investments = PropertyCardSerializer(many=True)


class InvestmentScreenResponseSerializer(serializers.Serializer):
    """Structure de réponse pour l'Écran 13 (Investir)."""

    top_yield_properties = PropertyCardSerializer(many=True)
    furnished_residences = PropertyCardSerializer(many=True)
    development_projects = DevelopmentProjectSummarySerializer(many=True)
    land_opportunities = PropertyCardSerializer(many=True)


class FavoriteToggleResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    is_favorited = serializers.BooleanField()


class PropertyFavoriteAdminSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    property_title = serializers.CharField(source="property.title", read_only=True)
    property_reference = serializers.CharField(source="property.reference", read_only=True)
    property_price = serializers.DecimalField(source="property.price", max_digits=14, decimal_places=2, read_only=True)
    property_commune = serializers.CharField(source="property.commune", read_only=True)

    class Meta:
        model = PropertyFavorite
        fields = [
            "id",
            "user",
            "user_email",
            "user_name",
            "property",
            "property_title",
            "property_reference",
            "property_price",
            "property_commune",
            "created_at",
        ]

    @extend_schema_field({"type": "string"})
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class PlacesResponseSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["commune", "quartier"])
    name = serializers.CharField()
    commune = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    count = serializers.IntegerField()
