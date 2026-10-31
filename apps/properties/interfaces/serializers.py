from rest_framework import serializers
from apps.properties.infrastructure.models import (
    Property, PropertyImage, PropertyFavorite,
    DevelopmentProject, ProjectLot
)

class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'caption', 'is_cover', 'order']


class ProjectLotSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    typology_display = serializers.CharField(source='get_typology_display', read_only=True)

    class Meta:
        model = ProjectLot
        fields = ['id', 'lot_number', 'typology', 'typology_display', 'building_name', 'floor', 'surface_sqm', 'price', 'status', 'status_display']


class DevelopmentProjectSerializer(serializers.ModelSerializer):
    lots = ProjectLotSerializer(many=True, read_only=True)

    class Meta:
        model = DevelopmentProject
        fields = [
            'id', 'name', 'slug', 'developer_name', 'city', 'commune', 'neighborhood',
            'description', 'total_lots_count', 'delivery_date', 'starting_price',
            'cover_image', 'brochure_pdf', 'virtual_tour_url', 'is_featured', 'lots'
        ]


class PropertyCardSerializer(serializers.ModelSerializer):
    """
    Format standardisé pour les cartes de biens (Écran 04 Accueil, Écran 06 Résultats, Écran 13 Investir).
    Affiche : Photo, F3 - Cocody Abatta, 82 m², 66 000 000 FCFA, Investissement/Habitation, Bouton favori.
    """
    cover_image = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    typology_display = serializers.CharField(source='get_typology_display', read_only=True)
    target_goal_display = serializers.CharField(source='get_target_goal_display', read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'reference', 'title', 'slug', 'property_type', 'property_type_display',
            'typology', 'typology_display', 'target_goal', 'target_goal_display',
            'price', 'surface_sqm', 'commune', 'neighborhood',
            'estimated_monthly_rent', 'estimated_yield_rate', 'investment_score',
            'cover_image', 'is_favorited', 'verification_status', 'created_at'
        ]

    def get_cover_image(self, obj) -> str:
        first_img = obj.images.filter(is_cover=True).first() or obj.images.first()
        if first_img and first_img.image:
            request = self.context.get('request')
            return request.build_absolute_uri(first_img.image.url) if request else first_img.image.url
        return None

    def get_is_favorited(self, obj) -> bool:
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False


class PropertyDetailSerializer(serializers.ModelSerializer):
    """
    Fiche détaillée complète du bien (Écran 07 Fiche Bien).
    Galerie photos, vidéo, coordonnées, bloc investissement, équipements.
    """
    images = PropertyImageSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    property_type_display = serializers.CharField(source='get_property_type_display', read_only=True)
    typology_display = serializers.CharField(source='get_typology_display', read_only=True)
    target_goal_display = serializers.CharField(source='get_target_goal_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)

    class Meta:
        model = Property
        fields = '__all__'

    def get_is_favorited(self, obj) -> bool:
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False


class HomeScreenResponseSerializer(serializers.Serializer):
    """Structure de réponse globale pour l'Écran 04 (Accueil)."""
    featured_opportunities = PropertyCardSerializer(many=True)
    recent_properties = PropertyCardSerializer(many=True)
    development_projects = DevelopmentProjectSerializer(many=True)
    selected_investments = PropertyCardSerializer(many=True)


class InvestmentScreenResponseSerializer(serializers.Serializer):
    """Structure de réponse pour l'Écran 13 (Investir)."""
    top_yield_properties = PropertyCardSerializer(many=True)
    furnished_residences = PropertyCardSerializer(many=True)
    development_projects = DevelopmentProjectSerializer(many=True)
    land_opportunities = PropertyCardSerializer(many=True)


class FavoriteToggleResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    is_favorited = serializers.BooleanField()


class PropertyFavoriteAdminSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    property_title = serializers.CharField(source='property.title', read_only=True)
    property_reference = serializers.CharField(source='property.reference', read_only=True)
    property_price = serializers.DecimalField(source='property.price', max_digits=14, decimal_places=2, read_only=True)
    property_commune = serializers.CharField(source='property.commune', read_only=True)

    class Meta:
        model = PropertyFavorite
        fields = [
            'id', 'user', 'user_email', 'user_name', 'property',
            'property_title', 'property_reference', 'property_price',
            'property_commune', 'created_at'
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email

