from django.urls import path

from .views import AnalyticsSummaryView, EventIngestView

urlpatterns = [
    path("events/", EventIngestView.as_view(), name="analytics-events"),
    path("summary/", AnalyticsSummaryView.as_view(), name="analytics-summary"),
]
