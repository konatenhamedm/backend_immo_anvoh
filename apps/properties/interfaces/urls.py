from django.urls import path
from .views import (
    HomeScreenView,
    PropertySearchView,
    PropertyDetailView,
    InvestmentScreenView,
    DevelopmentProjectListView,
    DevelopmentProjectDetailView,
    ProjectLotListCreateView,
    ProjectLotDetailView,
    FavoritesListView,
    FavoriteToggleView,
    AdminPropertyFavoriteListView
)

urlpatterns = [
    # Écran 04 Accueil
    path('home/', HomeScreenView.as_view(), name='home-screen'),

    # Écran 05 & 06 Recherche & Résultats
    path('search/', PropertySearchView.as_view(), name='property-search'),

    # Écran 07 Fiche Bien
    path('<uuid:id>/', PropertyDetailView.as_view(), name='property-detail'),

    # Écran 13 Espace Investir
    path('invest/', InvestmentScreenView.as_view(), name='invest-screen'),

    # Programmes Neufs & Lots
    path('projects/', DevelopmentProjectListView.as_view(), name='projects-list'),
    path('projects/<uuid:id>/', DevelopmentProjectDetailView.as_view(), name='projects-detail'),
    path('projects/<uuid:project_id>/lots/', ProjectLotListCreateView.as_view(), name='project-lots-list-create'),
    path('lots/<uuid:id>/', ProjectLotDetailView.as_view(), name='project-lot-detail'),

    # Écran 14 Favoris
    path('favorites/', FavoritesListView.as_view(), name='favorites-list'),
    path('favorites/<uuid:property_id>/toggle/', FavoriteToggleView.as_view(), name='favorite-toggle'),
    path('admin/favorites/', AdminPropertyFavoriteListView.as_view(), name='admin-favorites-list'),
]
