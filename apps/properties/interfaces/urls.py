from django.urls import path

from .views import (
    AdminPropertyDetailView,
    AdminPropertyFavoriteDetailView,
    AdminPropertyFavoriteListView,
    AdminPropertyListCreateView,
    CatalogMetaView,
    DevelopmentProjectBySlugView,
    ProjectDocumentCreateView,
    ProjectDocumentDeleteView,
    DevelopmentProjectDetailView,
    DevelopmentProjectListView,
    FavoritesListView,
    FavoriteToggleView,
    HomeScreenView,
    InvestmentScreenView,
    OwnerDashboardView,
    OwnerPropertyDetailView,
    OwnerPropertyListCreateView,
    ProjectLotDetailView,
    ProjectLotListCreateView,
    PropertyBySlugView,
    PropertyDetailView,
    PropertyImageDetailView,
    PropertyImageUploadView,
    PropertySearchView,
    PropertySlugListView,
)

urlpatterns = [
    # Catalogue public
    path("home/", HomeScreenView.as_view(), name="home-screen"),
    path("search/", PropertySearchView.as_view(), name="property-search"),
    path("meta/", CatalogMetaView.as_view(), name="catalog-meta"),
    path("slugs/", PropertySlugListView.as_view(), name="property-slugs"),
    path("slug/<slug:slug>/", PropertyBySlugView.as_view(), name="property-by-slug"),
    path("<uuid:id>/", PropertyDetailView.as_view(), name="property-detail"),
    path("<uuid:id>/images/", PropertyImageUploadView.as_view(), name="property-image-upload"),
    path("images/<uuid:id>/", PropertyImageDetailView.as_view(), name="property-image-detail"),
    path("invest/", InvestmentScreenView.as_view(), name="invest-screen"),
    # Programmes neufs & lots
    path("projects/", DevelopmentProjectListView.as_view(), name="projects-list"),
    path("projects/slug/<slug:slug>/", DevelopmentProjectBySlugView.as_view(), name="projects-by-slug"),
    path("projects/<uuid:id>/", DevelopmentProjectDetailView.as_view(), name="projects-detail"),
    path("projects/<uuid:project_id>/documents/", ProjectDocumentCreateView.as_view(), name="project-documents-create"),
    path("projects/documents/<uuid:id>/", ProjectDocumentDeleteView.as_view(), name="project-documents-delete"),
    path("projects/<uuid:project_id>/lots/", ProjectLotListCreateView.as_view(), name="project-lots-list-create"),
    path("lots/<uuid:id>/", ProjectLotDetailView.as_view(), name="project-lot-detail"),
    # Favoris
    path("favorites/", FavoritesListView.as_view(), name="favorites-list"),
    path("favorites/<uuid:property_id>/toggle/", FavoriteToggleView.as_view(), name="favorite-toggle"),
    # Espace propriétaire
    path("owner/", OwnerPropertyListCreateView.as_view(), name="owner-properties"),
    path("owner/dashboard/", OwnerDashboardView.as_view(), name="owner-dashboard"),
    path("owner/<uuid:id>/", OwnerPropertyDetailView.as_view(), name="owner-property-detail"),
    # Back-office
    path("admin/properties/", AdminPropertyListCreateView.as_view(), name="admin-properties"),
    path("admin/properties/<uuid:id>/", AdminPropertyDetailView.as_view(), name="admin-property-detail"),
    path("admin/favorites/", AdminPropertyFavoriteListView.as_view(), name="admin-favorites-list"),
    path("admin/favorites/<uuid:id>/", AdminPropertyFavoriteDetailView.as_view(), name="admin-favorite-detail"),
]
