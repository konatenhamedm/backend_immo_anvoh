"""Vues de `properties`, réparties par public. Les `urls.py` importent toujours `from .views import …`."""

from .admin import AdminPropertyDetailView, AdminPropertyListCreateView
from .catalog import (
    CatalogMetaView,
    HomeScreenView,
    InvestmentScreenView,
    PropertyBySlugView,
    PropertyDetailView,
    PropertySearchView,
    PropertySlugListView,
)
from .favorites import (
    AdminPropertyFavoriteDetailView,
    AdminPropertyFavoriteListView,
    FavoritesListView,
    FavoriteToggleView,
)
from .images import PropertyImageDetailView, PropertyImageUploadView
from .owner import OwnerDashboardView, OwnerPropertyDetailView, OwnerPropertyListCreateView
from .projects import (
    DevelopmentProjectBySlugView,
    ProjectDocumentCreateView,
    ProjectDocumentDeleteView,
    DevelopmentProjectDetailView,
    DevelopmentProjectListView,
    ProjectLotDetailView,
    ProjectLotListCreateView,
)

__all__ = [
    "HomeScreenView",
    "PropertySearchView",
    "PropertyDetailView",
    "PropertyBySlugView",
    "PropertySlugListView",
    "CatalogMetaView",
    "InvestmentScreenView",
    "DevelopmentProjectListView",
    "DevelopmentProjectDetailView",
    "DevelopmentProjectBySlugView",
    "ProjectDocumentCreateView",
    "ProjectDocumentDeleteView",
    "ProjectLotListCreateView",
    "ProjectLotDetailView",
    "FavoritesListView",
    "FavoriteToggleView",
    "AdminPropertyFavoriteListView",
    "AdminPropertyFavoriteDetailView",
    "OwnerPropertyListCreateView",
    "OwnerPropertyDetailView",
    "OwnerDashboardView",
    "PropertyImageUploadView",
    "PropertyImageDetailView",
    "AdminPropertyListCreateView",
    "AdminPropertyDetailView",
]
