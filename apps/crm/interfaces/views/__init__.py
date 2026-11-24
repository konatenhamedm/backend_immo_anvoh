"""Vues de `crm`, réparties par public. Les `urls.py` importent toujours `from .views import …`."""

from .admin_dashboard import AdminDashboardView, GlobalSearchView
from .admin_leads import LeadCreateAdminView, LeadDetailAdminView, LeadNoteView, PipelineKanbanView
from .admin_requests import (
    PropertyInquiryDetailAdminView,
    PropertyInquiryListAdminView,
    VisitRequestDetailAdminView,
    VisitRequestListAdminView,
)
from .buyer import MyRequestsView, MyVisitCancelView, SearchAlertDetailView, SearchAlertListCreateView
from .owner import OwnerVisitListView, OwnerVisitUpdateView
from .public_forms import DiasporaContactView, FindMyPropertyView, PropertyInquiryView, ScheduleVisitView, WhatsAppClickTrackView

__all__ = [
    "PropertyInquiryView",
    "WhatsAppClickTrackView",
    "DiasporaContactView",
    "FindMyPropertyView",
    "ScheduleVisitView",
    "MyRequestsView",
    "MyVisitCancelView",
    "SearchAlertListCreateView",
    "SearchAlertDetailView",
    "OwnerVisitListView",
    "OwnerVisitUpdateView",
    "PipelineKanbanView",
    "LeadDetailAdminView",
    "LeadNoteView",
    "LeadCreateAdminView",
    "VisitRequestListAdminView",
    "VisitRequestDetailAdminView",
    "PropertyInquiryListAdminView",
    "PropertyInquiryDetailAdminView",
    "AdminDashboardView",
    "GlobalSearchView",
]
