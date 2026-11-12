from datetime import timedelta

from django.db.models import Count, F, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.interfaces.permissions import IsOwnerRole, IsStaffOrAgent, ReadOnlyOr, is_admin, is_staff_or_agent
from apps.properties.infrastructure.models import (
    Property, PropertyFavorite, PropertyImage, PropertyStatus, VerificationStatus, PUBLIC_STATUSES,
    DevelopmentProject, ProjectLot, PropertyType, TransactionType, TitleDeedType,
)
from .serializers import (
    PropertyCardSerializer,
    PropertyDetailSerializer,
    PropertyWriteSerializer,
    PropertyAdminWriteSerializer,
    PropertyImageSerializer,
    ImageUploadSerializer,
    HomeScreenResponseSerializer,
    InvestmentScreenResponseSerializer,
    DevelopmentProjectSerializer,
    ProjectLotSerializer,
    FavoriteToggleResponseSerializer,
    PropertyFavoriteAdminSerializer,
    favorite_ids_for,
)

DEFAULT_COMMUNES = ["Cocody", "Marcory", "Plateau", "Yopougon", "Bingerville", "Grand-Bassam", "Assinie", "Songon"]
MONTHS_FR = ['Janv.', 'Févr.', 'Mars', 'Avr.', 'Mai', 'Juin', 'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.']
# Champs dont la modification relance la vérification notariale d'un bien déjà certifié.
SENSITIVE_FIELDS = ('commune', 'neighborhood', 'surface_sqm', 'property_type', 'title_deed')


def cards_qs():
    return Property.objects.select_related('owner', 'assigned_agent', 'accreditation__notary').prefetch_related('images')


def public_qs():
    return cards_qs().filter(status__in=PUBLIC_STATUSES)


def ctx(request):
    return {'request': request, 'favorite_ids': favorite_ids_for(request)}


def can_manage(user, prop) -> bool:
    return is_staff_or_agent(user) or (user.is_authenticated and prop.owner_id == user.id)


def apply_search_filters(qs, params):
    q = params.get('q')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(commune__icontains=q) | Q(neighborhood__icontains=q) | Q(description__icontains=q) | Q(reference__icontains=q))
    for param, lookup in (('commune', 'commune__icontains'), ('neighborhood', 'neighborhood__icontains'),
                          ('type', 'property_type'), ('typology', 'typology'), ('target_goal', 'target_goal'),
                          ('transaction', 'transaction'), ('min_price', 'price__gte'), ('max_price', 'price__lte'),
                          ('min_surface', 'surface_sqm__gte'), ('rooms_count', 'rooms_count'), ('min_bedrooms', 'bedrooms_count__gte')):
        if params.get(param):
            qs = qs.filter(**{lookup: params[param]})
    if params.get('verified') in ('1', 'true'):
        qs = qs.filter(verification_status__in=[VerificationStatus.VERIFIE, VerificationStatus.VERIFICATION_RENFORCEE])
    if params.get('has_tour') in ('1', 'true'):
        qs = qs.exclude(virtual_tour_url__isnull=True).exclude(virtual_tour_url='')
    ordering = params.get('ordering', '-created_at')
    allowed = ['price', '-price', 'created_at', '-created_at', '-estimated_yield_rate', '-investment_score', '-views_count']
    return qs.order_by(ordering if ordering in allowed else '-created_at')


# ---------------------------------------------------------------------------
# Catalogue public
# ---------------------------------------------------------------------------

@extend_schema(tags=["Catalogue & Écrans"], summary="Données globales de l'Écran 04 (Accueil)", responses={200: HomeScreenResponseSerializer})
class HomeScreenView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        active = public_qs().filter(status=PropertyStatus.DISPONIBLE)
        projects = DevelopmentProject.objects.prefetch_related('lots')[:4]
        c = ctx(request)
        return Response({
            'featured_opportunities': PropertyCardSerializer(active.filter(is_featured=True)[:6], many=True, context=c).data,
            'recent_properties': PropertyCardSerializer(active.order_by('-created_at')[:8], many=True, context=c).data,
            'development_projects': DevelopmentProjectSerializer(projects, many=True, context=c).data,
            'selected_investments': PropertyCardSerializer(active.filter(is_selected_investment=True)[:6], many=True, context=c).data,
        })


@extend_schema(
    tags=["Catalogue & Écrans"],
    summary="Moteur de recherche (Écrans 05 & 06) — création réservée à l'équipe",
    parameters=[
        OpenApiParameter('q', str), OpenApiParameter('commune', str), OpenApiParameter('neighborhood', str),
        OpenApiParameter('type', str), OpenApiParameter('typology', str), OpenApiParameter('target_goal', str),
        OpenApiParameter('transaction', str, description="VENTE | LOCATION"),
        OpenApiParameter('min_price', float), OpenApiParameter('max_price', float), OpenApiParameter('min_surface', float),
        OpenApiParameter('rooms_count', int), OpenApiParameter('min_bedrooms', int),
        OpenApiParameter('verified', bool), OpenApiParameter('has_tour', bool),
        OpenApiParameter('ordering', str), OpenApiParameter('page_size', int, description="Jusqu'à 100"),
    ],
    responses={200: PropertyCardSerializer(many=True)}
)
class PropertySearchView(generics.ListCreateAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]

    def get_serializer_class(self):
        return PropertyAdminWriteSerializer if self.request.method == 'POST' else PropertyCardSerializer

    def get_serializer_context(self):
        return ctx(self.request) if self.request.method == 'GET' else super().get_serializer_context()

    def get_queryset(self):
        return apply_search_filters(public_qs(), self.request.query_params)


def _visible_or_404(request, prop):
    if not prop.is_public and not can_manage(request.user, prop):
        raise NotFound('Bien introuvable')
    return prop


@extend_schema(tags=["Catalogue & Écrans"], summary="Fiche d'un bien par identifiant (modification réservée à l'équipe)")
class PropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    queryset = cards_qs().select_related('development_project')
    lookup_field = 'id'

    def get_serializer_class(self):
        return PropertyDetailSerializer if self.request.method == 'GET' else PropertyAdminWriteSerializer

    def get_object(self):
        return _visible_or_404(self.request, super().get_object())

    def get_serializer_context(self):
        return ctx(self.request)


@extend_schema(tags=["Catalogue & Écrans"], summary="Fiche d'un bien par slug (URL du site) — compte une vue", responses={200: PropertyDetailSerializer})
class PropertyBySlugView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        prop = _visible_or_404(request, get_object_or_404(cards_qs().select_related('development_project'), slug=slug))
        if prop.is_public and not can_manage(request.user, prop) and request.query_params.get('count_view', '1') != '0':
            Property.objects.filter(pk=prop.pk).update(views_count=F('views_count') + 1)
        return Response(PropertyDetailSerializer(prop, context=ctx(request)).data)


@extend_schema(tags=["Catalogue & Écrans"], summary="Slugs des biens publiés (sitemap, pré-rendu)")
class PropertySlugListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        rows = Property.objects.filter(status__in=PUBLIC_STATUSES).values('slug', 'updated_at')
        return Response(list(rows))


@extend_schema(tags=["Catalogue & Écrans"], summary="Référentiels : communes, types, transactions, titres")
class CatalogMetaView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        used = Property.objects.filter(status__in=PUBLIC_STATUSES).values_list('commune', flat=True).distinct()
        communes = list(dict.fromkeys(DEFAULT_COMMUNES + sorted(c for c in used if c)))
        return Response({
            'communes': communes,
            'property_types': [{'value': v, 'label': l} for v, l in PropertyType.choices],
            'transactions': [{'value': v, 'label': l} for v, l in TransactionType.choices],
            'title_deeds': [{'value': v, 'label': l} for v, l in TitleDeedType.choices],
        })


@extend_schema(tags=["Catalogue & Écrans"], summary="Données de l'Écran 13 (Espace Investir)", responses={200: InvestmentScreenResponseSerializer})
class InvestmentScreenView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        active = public_qs().filter(status=PropertyStatus.DISPONIBLE)
        c = ctx(request)
        return Response({
            'top_yield_properties': PropertyCardSerializer(active.exclude(estimated_yield_rate__isnull=True).order_by('-estimated_yield_rate')[:6], many=True, context=c).data,
            'furnished_residences': PropertyCardSerializer(active.filter(property_type=PropertyType.RESIDENCE_MEUBLEE)[:6], many=True, context=c).data,
            'development_projects': DevelopmentProjectSerializer(DevelopmentProject.objects.prefetch_related('lots')[:6], many=True, context=c).data,
            'land_opportunities': PropertyCardSerializer(active.filter(property_type=PropertyType.TERRAIN)[:6], many=True, context=c).data,
        })


# ---------------------------------------------------------------------------
# Programmes neufs (lecture publique, écriture équipe)
# ---------------------------------------------------------------------------

@extend_schema(tags=["Programmes Neufs"])
class DevelopmentProjectListView(generics.ListCreateAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    queryset = DevelopmentProject.objects.prefetch_related('lots')
    serializer_class = DevelopmentProjectSerializer


@extend_schema(tags=["Programmes Neufs"])
class DevelopmentProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    queryset = DevelopmentProject.objects.prefetch_related('lots')
    serializer_class = DevelopmentProjectSerializer
    lookup_field = 'id'


@extend_schema(tags=["Programmes Neufs"])
class ProjectLotListCreateView(generics.ListCreateAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    serializer_class = ProjectLotSerializer
    pagination_class = None

    def get_queryset(self):
        return ProjectLot.objects.filter(project_id=self.kwargs.get('project_id'))

    def perform_create(self, serializer):
        serializer.save(project=get_object_or_404(DevelopmentProject, id=self.kwargs.get('project_id')))


@extend_schema(tags=["Programmes Neufs"])
class ProjectLotDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [ReadOnlyOr(IsStaffOrAgent)]
    queryset = ProjectLot.objects.all()
    serializer_class = ProjectLotSerializer
    lookup_field = 'id'


# ---------------------------------------------------------------------------
# Favoris
# ---------------------------------------------------------------------------

@extend_schema(tags=["Favoris"])
class FavoritesListView(generics.ListAPIView):
    """Écran 14 : biens favoris de l'utilisateur connecté (encore publiés)."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PropertyCardSerializer
    pagination_class = None

    def get_queryset(self):
        return public_qs().filter(favorited_by__user=self.request.user)

    def get_serializer_context(self):
        return ctx(self.request)


@extend_schema(tags=["Favoris"], summary="Ajouter ou retirer un bien des favoris", request=None,
               responses={200: FavoriteToggleResponseSerializer, 201: FavoriteToggleResponseSerializer})
class FavoriteToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, property_id):
        prop = get_object_or_404(Property, id=property_id, status__in=PUBLIC_STATUSES)
        fav, created = PropertyFavorite.objects.get_or_create(user=request.user, property=prop)
        if not created:
            fav.delete()
            return Response({'status': 'removed', 'is_favorited': False}, status=status.HTTP_200_OK)
        return Response({'status': 'added', 'is_favorited': True}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Back-office Favoris"])
class AdminPropertyFavoriteListView(generics.ListAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = PropertyFavorite.objects.select_related('property', 'user').order_by('-created_at')
    serializer_class = PropertyFavoriteAdminSerializer


@extend_schema(tags=["Back-office Favoris"])
class AdminPropertyFavoriteDetailView(generics.DestroyAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = PropertyFavorite.objects.all()
    lookup_field = 'id'


# ---------------------------------------------------------------------------
# Espace propriétaire
# ---------------------------------------------------------------------------

def owner_qs(user):
    return cards_qs().filter(owner=user).annotate(leads_count=Count('leads', distinct=True))


@extend_schema(tags=["Espace Propriétaire"], summary="Mes biens / publier un bien (part en vérification notariale)")
class OwnerPropertyListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOwnerRole]
    pagination_class = None

    def get_serializer_class(self):
        return PropertyWriteSerializer if self.request.method == 'POST' else PropertyCardSerializer

    def get_serializer_context(self):
        return ctx(self.request)

    def get_queryset(self):
        return owner_qs(self.request.user).exclude(status=PropertyStatus.ARCHIVE)

    def create(self, request, *args, **kwargs):
        from apps.accreditation.domain.services import ensure_file
        serializer = PropertyWriteSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        draft = request.data.get('draft') in (True, 'true', '1')
        prop = serializer.save(
            owner=request.user,
            status=PropertyStatus.BROUILLON if draft else PropertyStatus.EN_ATTENTE,
            verification_status=VerificationStatus.NON_VERIFIE if draft else VerificationStatus.EN_ATTENTE,
            is_featured=False, is_selected_investment=False,
        )
        if not draft:
            ensure_file(prop)
        prop = owner_qs(request.user).get(pk=prop.pk)
        return Response(PropertyDetailSerializer(prop, context=ctx(request)).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Espace Propriétaire"], summary="Consulter / modifier / retirer un de mes biens")
class OwnerPropertyDetailView(APIView):
    permission_classes = [IsOwnerRole]

    def _get(self, request, id):
        prop = get_object_or_404(owner_qs(request.user) if not is_admin(request.user) else cards_qs(), id=id)
        return prop

    @extend_schema(responses={200: PropertyDetailSerializer})
    def get(self, request, id):
        return Response(PropertyDetailSerializer(self._get(request, id), context=ctx(request)).data)

    @extend_schema(request=PropertyWriteSerializer, responses={200: PropertyDetailSerializer})
    def patch(self, request, id):
        from apps.accreditation.domain.services import ensure_file
        from apps.accreditation.infrastructure.models import AccreditationStatus, AccreditationStep
        prop = self._get(request, id)
        before = {f: getattr(prop, f) for f in SENSITIVE_FIELDS}
        serializer = PropertyWriteSerializer(prop, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        prop = serializer.save()

        submit = request.data.get('submit') in (True, 'true', '1')
        changed = any(getattr(prop, f) != v for f, v in before.items())
        file = getattr(prop, 'accreditation', None)  # RelatedObjectDoesNotExist hérite d'AttributeError
        if submit and prop.status == PropertyStatus.BROUILLON:
            ensure_file(prop)  # brouillon soumis (ou correction après refus)
        elif changed and file and file.status == AccreditationStatus.CERTIFIE:
            # Le bien reste en ligne, mais le notaire revérifie le dossier.
            file.status, file.step = AccreditationStatus.EN_COURS, AccreditationStep.CONTROLE_JURIDIQUE
            file.save(update_fields=['status', 'step', 'updated_at'])
            prop.verification_status = VerificationStatus.EN_ATTENTE
            prop.save(update_fields=['verification_status', 'updated_at'])
        return Response(PropertyDetailSerializer(self._get(request, id), context=ctx(request)).data)

    def delete(self, request, id):
        prop = self._get(request, id)
        if prop.status in (PropertyStatus.RESERVE, PropertyStatus.VENDU):
            return Response({'detail': "Un bien réservé ou vendu ne peut pas être retiré."}, status=status.HTTP_400_BAD_REQUEST)
        prop.status = PropertyStatus.ARCHIVE
        prop.save(update_fields=['status', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Espace Propriétaire"], summary="Vue d'ensemble : audience, demandes, visites, accréditations")
class OwnerDashboardView(APIView):
    permission_classes = [IsOwnerRole]

    def get(self, request):
        from apps.crm.infrastructure.models import Lead, VisitRequest, VisitRequestStatus
        from apps.accreditation.infrastructure.models import AccreditationFile, AccreditationStatus
        props = Property.objects.filter(owner=request.user).exclude(status=PropertyStatus.ARCHIVE)
        today = timezone.localdate()
        start = (today.replace(day=1) - timedelta(days=150)).replace(day=1)
        leads_by_month = dict(
            Lead.objects.filter(consulted_property__owner=request.user, created_at__date__gte=start)
            .annotate(m=TruncMonth('created_at')).values('m').annotate(n=Count('id')).values_list('m', 'n')
        )
        months, cursor = [], start
        while cursor <= today:
            key = next((k for k in leads_by_month if k.year == cursor.year and k.month == cursor.month), None)
            months.append({'month': MONTHS_FR[cursor.month - 1], 'value': leads_by_month.get(key, 0) if key else 0})
            cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
        return Response({
            'properties_total': props.count(),
            'properties_online': props.filter(status__in=PUBLIC_STATUSES).count(),
            'views_total': sum(props.values_list('views_count', flat=True)),
            'leads_total': Lead.objects.filter(consulted_property__owner=request.user).count(),
            'visits_pending': VisitRequest.objects.filter(property__owner=request.user, status=VisitRequestStatus.EN_ATTENTE).count(),
            'visits_upcoming': VisitRequest.objects.filter(property__owner=request.user, status=VisitRequestStatus.CONFIRMEE, scheduled_date__gte=today).count(),
            'accreditations_in_progress': AccreditationFile.objects.filter(property__owner=request.user, status=AccreditationStatus.EN_COURS).count(),
            'monthly_leads': months[-6:],
        })


# ---------------------------------------------------------------------------
# Photos (propriétaire du bien ou équipe)
# ---------------------------------------------------------------------------

@extend_schema(tags=["Espace Propriétaire"], request=ImageUploadSerializer, responses={201: PropertyImageSerializer},
               summary="Ajouter une photo (fichier multipart ou URL externe)")
class PropertyImageUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, id):
        prop = get_object_or_404(Property, id=id)
        if not can_manage(request.user, prop):
            raise PermissionDenied("Ce bien ne vous appartient pas.")
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        is_cover = d.get('is_cover') or not prop.images.exists()
        if is_cover:
            prop.images.update(is_cover=False)
        img = PropertyImage.objects.create(
            property=prop, image=d.get('image'), external_url=d.get('external_url', ''), caption=d.get('caption', ''),
            is_cover=is_cover, order=prop.images.count(),
        )
        return Response(PropertyImageSerializer(img, context={'request': request}).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Espace Propriétaire"], summary="Supprimer une photo / la mettre en couverture (PATCH is_cover)")
class PropertyImageDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get(self, request, id):
        img = get_object_or_404(PropertyImage.objects.select_related('property'), id=id)
        if not can_manage(request.user, img.property):
            raise PermissionDenied("Ce bien ne vous appartient pas.")
        return img

    def patch(self, request, id):
        img = self._get(request, id)
        if request.data.get('is_cover'):
            img.property.images.update(is_cover=False)
            img.is_cover = True
            img.save(update_fields=['is_cover'])
        return Response(PropertyImageSerializer(img, context={'request': request}).data)

    def delete(self, request, id):
        self._get(request, id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Back-office catalogue
# ---------------------------------------------------------------------------

@extend_schema(tags=["Back-office Catalogue"],
               summary="Tous les biens, quel que soit leur statut (?q, status, verification, commune, type, tour=requested|published)")
class AdminPropertyListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsStaffOrAgent]

    def get_serializer_class(self):
        return PropertyAdminWriteSerializer if self.request.method == 'POST' else PropertyCardSerializer

    def get_serializer_context(self):
        return ctx(self.request)

    def get_queryset(self):
        params = self.request.query_params
        qs = cards_qs().annotate(leads_count=Count('leads', distinct=True))
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        if params.get('verification'):
            qs = qs.filter(verification_status=params['verification'])
        tour = params.get('tour')
        if tour == 'published':
            qs = qs.exclude(virtual_tour_url__isnull=True).exclude(virtual_tour_url='')
        elif tour == 'requested':
            qs = qs.filter(tour_scan_requested=True).filter(Q(virtual_tour_url__isnull=True) | Q(virtual_tour_url=''))
        return apply_search_filters(qs, params)


@extend_schema(tags=["Back-office Catalogue"])
class AdminPropertyDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsStaffOrAgent]
    queryset = cards_qs().select_related('development_project')
    lookup_field = 'id'

    def get_serializer_class(self):
        return PropertyDetailSerializer if self.request.method == 'GET' else PropertyAdminWriteSerializer

    def get_serializer_context(self):
        return ctx(self.request)
