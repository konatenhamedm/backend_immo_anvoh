from django.urls import path

from .views import (
    AccreditationActionView,
    AccreditationQueueView,
    DocumentReviewView,
    NotaryAdminDetailView,
    NotaryAdminListCreateView,
    NotaryPublicListView,
    OwnerAccreditationListView,
    OwnerDocumentDeleteView,
    OwnerDocumentUploadView,
)

urlpatterns = [
    path("notaries/", NotaryPublicListView.as_view(), name="notaries-public"),
    path("admin/notaries/", NotaryAdminListCreateView.as_view(), name="admin-notaries"),
    path("admin/notaries/<uuid:id>/", NotaryAdminDetailView.as_view(), name="admin-notary-detail"),
    path("owner/files/", OwnerAccreditationListView.as_view(), name="owner-accreditations"),
    path(
        "owner/properties/<uuid:property_id>/documents/",
        OwnerDocumentUploadView.as_view(),
        name="owner-document-upload",
    ),
    path("owner/documents/<uuid:id>/", OwnerDocumentDeleteView.as_view(), name="owner-document-delete"),
    path("queue/", AccreditationQueueView.as_view(), name="accreditation-queue"),
    path("queue/<uuid:id>/", AccreditationActionView.as_view(), name="accreditation-action"),
    path("documents/<uuid:id>/", DocumentReviewView.as_view(), name="document-review"),
]
