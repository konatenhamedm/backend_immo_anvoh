from django.urls import path

from .views import (
    AdminDashboardView,
    FindMyPropertyView,
    GlobalSearchView,
    LeadCreateAdminView,
    LeadDetailAdminView,
    LeadNoteView,
    MyRequestsView,
    MyVisitCancelView,
    OwnerVisitListView,
    OwnerVisitUpdateView,
    PipelineKanbanView,
    PropertyInquiryDetailAdminView,
    PropertyInquiryListAdminView,
    PropertyInquiryView,
    ScheduleVisitView,
    SearchAlertDetailView,
    SearchAlertListCreateView,
    VisitRequestDetailAdminView,
    VisitRequestListAdminView,
    WhatsAppClickTrackView,
)

urlpatterns = [
    # Parcours client (public ou connecté)
    path("inquiries/", PropertyInquiryView.as_view(), name="property-inquiry"),
    path("whatsapp-click/", WhatsAppClickTrackView.as_view(), name="whatsapp-click-track"),
    path("find-my-property/", FindMyPropertyView.as_view(), name="find-my-property"),
    path("visits/schedule/", ScheduleVisitView.as_view(), name="schedule-visit"),
    path("my-requests/", MyRequestsView.as_view(), name="my-requests"),
    path("my-visits/<uuid:id>/cancel/", MyVisitCancelView.as_view(), name="my-visit-cancel"),
    path("alerts/", SearchAlertListCreateView.as_view(), name="search-alerts"),
    path("alerts/<uuid:id>/", SearchAlertDetailView.as_view(), name="search-alert-detail"),
    # Espace propriétaire
    path("owner/visits/", OwnerVisitListView.as_view(), name="owner-visits"),
    path("owner/visits/<uuid:id>/", OwnerVisitUpdateView.as_view(), name="owner-visit-update"),
    # Back-office
    path("admin/search/", GlobalSearchView.as_view(), name="admin-search"),
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("pipeline/kanban/", PipelineKanbanView.as_view(), name="pipeline-kanban"),
    path("leads/", LeadCreateAdminView.as_view(), name="admin-lead-create"),
    path("leads/<uuid:id>/", LeadDetailAdminView.as_view(), name="admin-lead-detail"),
    path("leads/<uuid:id>/notes/", LeadNoteView.as_view(), name="admin-lead-notes"),
    path("visits/", VisitRequestListAdminView.as_view(), name="admin-visits-list"),
    path("visits/<uuid:id>/", VisitRequestDetailAdminView.as_view(), name="admin-visit-detail"),
    path("inquiries/list/", PropertyInquiryListAdminView.as_view(), name="admin-inquiries-list"),
    path("inquiries/<uuid:id>/", PropertyInquiryDetailAdminView.as_view(), name="admin-inquiry-detail"),
]
