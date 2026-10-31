from django.urls import path
from .views import (
    PropertyInquiryView,
    WhatsAppClickTrackView,
    FindMyPropertyView,
    ScheduleVisitView,
    MyRequestsView,
    PipelineKanbanView,
    LeadDetailAdminView,
    VisitRequestListAdminView,
    VisitRequestDetailAdminView,
    PropertyInquiryListAdminView
)

urlpatterns = [
    # Écran 08 Demande d'informations sur fiche bien
    path('inquiries/', PropertyInquiryView.as_view(), name='property-inquiry'),

    # Écran 09 Tracking clic WhatsApp
    path('whatsapp-click/', WhatsAppClickTrackView.as_view(), name='whatsapp-click-track'),

    # Écran 10 Formulaire Trouver mon bien (Questionnaire 7 étapes)
    path('find-my-property/', FindMyPropertyView.as_view(), name='find-my-property'),

    # Écran 16 Prise de RDV / Demande de visite
    path('visits/schedule/', ScheduleVisitView.as_view(), name='schedule-visit'),

    # Écran 15 Espace client "Mes demandes"
    path('my-requests/', MyRequestsView.as_view(), name='my-requests'),

    # Écran 26 Back-office Pipeline Kanban & Leads
    path('pipeline/kanban/', PipelineKanbanView.as_view(), name='pipeline-kanban'),
    path('leads/<uuid:id>/', LeadDetailAdminView.as_view(), name='admin-lead-detail'),
    path('visits/', VisitRequestListAdminView.as_view(), name='admin-visits-list'),
    path('visits/<uuid:id>/', VisitRequestDetailAdminView.as_view(), name='admin-visit-detail'),
    path('inquiries/list/', PropertyInquiryListAdminView.as_view(), name='admin-inquiries-list'),
]
