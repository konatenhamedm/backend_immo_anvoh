from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.properties.infrastructure.models import (
    Property, PropertyFavorite, PropertyStatus,
    DevelopmentProject, ProjectLot, PropertyType
)
from .serializers import (
    PropertyCardSerializer,
    PropertyDetailSerializer,
    HomeScreenResponseSerializer,
    InvestmentScreenResponseSerializer,
    DevelopmentProjectSerializer,
    ProjectLotSerializer,
    FavoriteToggleResponseSerializer,
    PropertyFavoriteAdminSerializer
)

@extend_schema(
    tags=["Catalogue & Écrans"],
    summary="Données globales de l'Écran 04 (Accueil)",
    description="Renvoie les opportunités du moment, biens récents, programmes neufs et investissements sélectionnés en 1 seul appel.",
    responses={200: HomeScreenResponseSerializer}
)
class HomeScreenView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        active_props = Property.objects.filter(status=PropertyStatus.DISPONIBLE).prefetch_related('images', 'favorited_by')
        
        featured = active_props.filter(is_featured=True)[:6]
        recent = active_props.order_by('-created_at')[:8]
        investments = active_props.filter(is_selected_investment=True)[:6]
        projects = DevelopmentProject.objects.all().prefetch_related('lots')[:4]

        data = {
            'featured_opportunities': PropertyCardSerializer(featured, many=True, context={'request': request}).data,
            'recent_properties': PropertyCardSerializer(recent, many=True, context={'request': request}).data,
            'development_projects': DevelopmentProjectSerializer(projects, many=True, context={'request': request}).data,
            'selected_investments': PropertyCardSerializer(investments, many=True, context={'request': request}).data,
        }
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Catalogue & Écrans"],
    summary="Moteur de recherche et résultats (Écrans 05 & 06)",
    parameters=[
        OpenApiParameter('q', str, description="Recherche globale texte (ex: 'Cocody Abatta')"),
        OpenApiParameter('commune', str, description="Commune (ex: Cocody, Bingerville)"),
        OpenApiParameter('neighborhood', str, description="Quartier (ex: Abatta, Angré)"),
        OpenApiParameter('type', str, description="Type de bien (APPARTEMENT, VILLA, TERRAIN...)"),
        OpenApiParameter('typology', str, description="Typologie (F2, F3, F4, F5)"),
        OpenApiParameter('target_goal', str, description="Objectif (HABITATION, INVESTISSEMENT, LOCATION)"),
        OpenApiParameter('min_price', float, description="Budget minimum"),
        OpenApiParameter('max_price', float, description="Budget maximum"),
        OpenApiParameter('min_surface', float, description="Superficie minimum en m²"),
        OpenApiParameter('rooms_count', int, description="Nombre de pièces"),
        OpenApiParameter('ordering', str, description="Tri : 'created_at', '-created_at', 'price', '-price'"),
    ],
    responses={200: PropertyCardSerializer(many=True)}
)
class PropertySearchView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PropertyDetailSerializer
        return PropertyCardSerializer

    def get_queryset(self):
        qs = Property.objects.filter(status=PropertyStatus.DISPONIBLE).prefetch_related('images', 'favorited_by')
        params = self.request.query_params

        # Recherche texte globale
        q = params.get('q')
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(commune__icontains=q) |
                Q(neighborhood__icontains=q) |
                Q(description__icontains=q)
            )

        # Filtres spécifiques
        if params.get('commune'):
            qs = qs.filter(commune__icontains=params.get('commune'))
        if params.get('neighborhood'):
            qs = qs.filter(neighborhood__icontains=params.get('neighborhood'))
        if params.get('type'):
            qs = qs.filter(property_type=params.get('type'))
        if params.get('typology'):
            qs = qs.filter(typology=params.get('typology'))
        if params.get('target_goal'):
            qs = qs.filter(target_goal=params.get('target_goal'))
        if params.get('min_price'):
            qs = qs.filter(price__gte=params.get('min_price'))
        if params.get('max_price'):
            qs = qs.filter(price__lte=params.get('max_price'))
        if params.get('min_surface'):
            qs = qs.filter(surface_sqm__gte=params.get('min_surface'))
        if params.get('rooms_count'):
            qs = qs.filter(rooms_count=params.get('rooms_count'))

        # Tri (Écran 05 : plus récent, prix croissant, prix décroissant)
        ordering = params.get('ordering', '-created_at')
        if ordering in ['price', '-price', 'created_at', '-created_at', '-estimated_yield_rate']:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by('-created_at')

        return qs


@extend_schema(
    tags=["Catalogue & Écrans"],
    summary="Fiche détaillée d'un bien (Écran 07)",
    responses={200: PropertyDetailSerializer}
)
class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Property.objects.all().prefetch_related('images', 'favorited_by')
    serializer_class = PropertyDetailSerializer
    lookup_field = 'id'


@extend_schema(
    tags=["Catalogue & Écrans"],
    summary="Données de l'Écran 13 (Espace Investir)",
    description="Regroupe : Meilleur rendement, Programmes neufs, Résidences meublées, Terrains à potentiel.",
    responses={200: InvestmentScreenResponseSerializer}
)
class InvestmentScreenView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        active_props = Property.objects.filter(status=PropertyStatus.DISPONIBLE).prefetch_related('images', 'favorited_by')
        
        top_yield = active_props.order_by('-estimated_yield_rate')[:6]
        furnished = active_props.filter(property_type=PropertyType.RESIDENCE_MEUBLEE)[:6]
        lands = active_props.filter(property_type=PropertyType.TERRAIN)[:6]
        projects = DevelopmentProject.objects.all().prefetch_related('lots')[:6]

        data = {
            'top_yield_properties': PropertyCardSerializer(top_yield, many=True, context={'request': request}).data,
            'furnished_residences': PropertyCardSerializer(furnished, many=True, context={'request': request}).data,
            'development_projects': DevelopmentProjectSerializer(projects, many=True, context={'request': request}).data,
            'land_opportunities': PropertyCardSerializer(lands, many=True, context={'request': request}).data,
        }
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=["Programmes Neufs"])
class DevelopmentProjectListView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = DevelopmentProject.objects.all().prefetch_related('lots')
    serializer_class = DevelopmentProjectSerializer


@extend_schema(tags=["Programmes Neufs"])
class DevelopmentProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = DevelopmentProject.objects.all().prefetch_related('lots')
    serializer_class = DevelopmentProjectSerializer
    lookup_field = 'id'


@extend_schema(tags=["Programmes Neufs"])
class ProjectLotListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProjectLotSerializer

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return ProjectLot.objects.filter(project_id=project_id)

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_id')
        project = DevelopmentProject.objects.get(id=project_id)
        serializer.save(project=project)


@extend_schema(tags=["Programmes Neufs"])
class ProjectLotDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = ProjectLot.objects.all()
    serializer_class = ProjectLotSerializer
    lookup_field = 'id'


@extend_schema(tags=["Favoris"])
class FavoritesListView(generics.ListAPIView):
    """Écran 14 : Liste des biens favoris de l'utilisateur connecté."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertyCardSerializer

    def get_queryset(self):
        user = self.request.user
        return Property.objects.filter(favorited_by__user=user).prefetch_related('images', 'favorited_by')


@extend_schema(
    tags=["Favoris"],
    summary="Ajouter ou retirer un bien des favoris",
    request=None,
    responses={200: FavoriteToggleResponseSerializer, 201: FavoriteToggleResponseSerializer}
)
class FavoriteToggleView(APIView):
    """Ajouter ou retirer un bien des favoris (Écran 06, 07, 14)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, property_id):
        try:
            prop = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            return Response({'detail': 'Bien introuvable'}, status=status.HTTP_404_NOT_FOUND)

        fav, created = PropertyFavorite.objects.get_or_create(user=request.user, property=prop)
        if not created:
            fav.delete()
            return Response({'status': 'removed', 'is_favorited': False}, status=status.HTTP_200_OK)
        return Response({'status': 'added', 'is_favorited': True}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Back-office Favoris"])
class AdminPropertyFavoriteListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = PropertyFavorite.objects.all().select_related('property', 'user').order_by('-created_at')
    serializer_class = PropertyFavoriteAdminSerializer
